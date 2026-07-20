#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPLAY=ROOT/"results/nexys3/p6_replay/p6_all_replay.csv"
P5_CYCLES=ROOT/"results/nexys3/p5_step8_b6/kernel_cycle_measurements.csv"
POLICY=ROOT/"results/rl/p3_export/policy_rom.mem"
PROFILE=ROOT/"results/rl/p3_export/profile_rom.mem"
TB=ROOT/"sim/spartan6/tb_p6_full_replay.v"
OUT=ROOT/"results/nexys3/p6_step3_golden_rtl"
GOLDEN=OUT/"golden_results.csv"
RTLCSV=OUT/"rtl_results.csv"
SUMMARY=OUT/"h0_h4_functional_summary.csv"
RESET_SPEC=OUT/"replay_reset_schedule.csv"
SIMLOG=ROOT/"evidence/nexys3/p6_step3_golden_rtl/rtl_simulation_raw.log"
COMPARELOG=ROOT/"evidence/nexys3/p6_step3_golden_rtl/exact_comparison.log"

FIELDS=["test_id","policy_id","state_id","profile_id","selected_path","score",
        "bottleneck_fidelity","cycles","status"]
RESET_IDS={0,5,10,1000}

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def read_csv(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path,fields,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def require(cond,label):
    if not cond:
        raise AssertionError(label)
    print("PASS",label)

def encode_state(r):
    def keyload(v):
        return 3 if v>=49151 else 2 if v>=32768 else 1 if v>=16384 else 0
    def fidelity(v):
        return 3 if v>=62914 else 2 if v>=60948 else 1 if v>=58982 else 0
    def imbalance(v):
        return 3 if v>=32768 else 2 if v>=16384 else 1 if v>=8192 else 0
    return (keyload(int(r["min_key_occupancy_u16"]))<<6) | \
           (fidelity(int(r["bottleneck_fidelity_state_u16"]))<<4) | \
           (keyload(int(r["offered_request_load_u16"]))<<2) | \
           imbalance(int(r["utilization_imbalance_state_u16"]))

def h3_action(sid):
    key=(sid>>6)&3
    fid=(sid>>4)&3
    load=(sid>>2)&3
    imb=sid&3
    if key==0: return 1
    if fid<=1: return 2
    if imb>=2: return 1
    if load==3 and key>=2 and fid>=2 and imb<=1: return 3
    return 0

def lambdas(payload):
    return ((payload>>4)&3,(payload>>2)&3,payload&3)

def normalized_pair(a,b):
    if a==b:
        return 0,0
    diff=abs(a-b)
    divisor=diff+1
    q=(diff*65535 + divisor//2)//divisor
    return (0,q) if a<b else (q,0)

def evaluator(r,lam):
    v0=int(r["c0_valid"])
    v1=int(r["c1_valid"])
    if not(v0 or v1):
        return 255,0,0
    if v0 and not v1:
        return int(r["c0_slot"]),0,int(r["c0_fidelity"])
    if v1 and not v0:
        return int(r["c1_slot"]),0,int(r["c1_fidelity"])
    objs0=[int(r["c0_cost"]),65535-int(r["c0_fidelity"]),int(r["c0_utilization"])]
    objs1=[int(r["c1_cost"]),65535-int(r["c1_fidelity"]),int(r["c1_utilization"])]
    n0=[]
    n1=[]
    for a,b in zip(objs0,objs1):
        x,y=normalized_pair(a,b)
        n0.append(x)
        n1.append(y)
    score0=max(n0[i]*lam[i] for i in range(3))
    score1=max(n1[i]*lam[i] for i in range(3))
    t0=(score0,int(r["c0_cost"]),int(r["c0_hops"]),int(r["c0_slot"]))
    t1=(score1,int(r["c1_cost"]),int(r["c1_hops"]),int(r["c1_slot"]))
    if t0<=t1:
        return int(r["c0_slot"]),score0,int(r["c0_fidelity"])
    return int(r["c1_slot"]),score1,int(r["c1_fidelity"])

def evaluator_latency(r):
    v0=int(r["c0_valid"])
    v1=int(r["c1_valid"])
    if not(v0 or v1):
        return 2
    if v0 != v1:
        return 3
    objs0=[int(r["c0_cost"]),65535-int(r["c0_fidelity"]),int(r["c0_utilization"])]
    objs1=[int(r["c1_cost"]),65535-int(r["c1_fidelity"]),int(r["c1_utilization"])]
    unequal=sum(a!=b for a,b in zip(objs0,objs1))
    return 5+100*unequal

def kernel_cycles(r,mode):
    if not int(r["input_valid"]):
        return 1
    if mode==0:
        return 2
    base=evaluator_latency(r)
    if mode==1:
        return base+4
    if mode in (2,3):
        return base+5
    return base+7

class H4:
    def __init__(self,policy):
        self.policy=policy
        self.reset()
    def reset(self):
        self.valid=False
        self.action=0
        self.dwell=0
    def choose(self,sid):
        proposed=self.policy[sid]
        eligible=self.valid and proposed!=self.action and self.dwell>=3
        if not self.valid:
            selected=proposed
        elif eligible:
            selected=proposed
        else:
            selected=self.action
        if not self.valid or eligible:
            dwell=1
        else:
            dwell=min(3,self.dwell+1)
        self.valid=True
        self.action=selected
        self.dwell=dwell
        return selected

def golden_rows(replay,policy,profiles):
    result=[]
    for mode in range(5):
        h4=H4(policy)
        for r in replay:
            tid=int(r["test_id"])
            if tid in RESET_IDS:
                h4.reset()
            if not int(r["input_valid"]):
                result.append(dict(test_id=tid,policy_id=mode,state_id=0,profile_id=0,
                  selected_path=255,score=0,bottleneck_fidelity=0,cycles=1,status=2))
                continue
            sid=encode_state(r)
            if mode==0:
                profile=0
                v0=int(r["c0_valid"])
                v1=int(r["c1_valid"])
                if not(v0 or v1):
                    path,score,bfid=255,0,0
                elif v0 and not v1:
                    path,score,bfid=int(r["c0_slot"]),0,int(r["c0_fidelity"])
                elif v1 and not v0:
                    path,score,bfid=int(r["c1_slot"]),0,int(r["c1_fidelity"])
                else:
                    t0=(int(r["c0_hops"]),int(r["c0_slot"]))
                    t1=(int(r["c1_hops"]),int(r["c1_slot"]))
                    if t0<=t1:
                        path,score,bfid=int(r["c0_slot"]),0,int(r["c0_fidelity"])
                    else:
                        path,score,bfid=int(r["c1_slot"]),0,int(r["c1_fidelity"])
            else:
                if mode==1:
                    profile=0
                    lam=(1,0,0)
                elif mode==2:
                    profile=0
                    lam=lambdas(profiles[0])
                elif mode==3:
                    profile=h3_action(sid)
                    lam=lambdas(profiles[profile])
                else:
                    profile=h4.choose(sid)
                    lam=lambdas(profiles[profile])
                path,score,bfid=evaluator(r,lam)
            status=1 if not(int(r["c0_valid"]) or int(r["c1_valid"])) else 0
            if status!=0:
                path,score,bfid=255,0,0
            result.append(dict(test_id=tid,policy_id=mode,state_id=sid,profile_id=profile,
              selected_path=path,score=score,bottleneck_fidelity=bfid,
              cycles=kernel_cycles(r,mode),status=status))
    return sorted(result,key=lambda x:(x["test_id"],x["policy_id"]))

def generate_tb(replay):
    head=r'''`timescale 1ns / 1ps
module tb_p6_full_replay;
reg clk,rst,start,input_valid;
reg [15:0] min_key,state_fid,load,imbalance;
reg v0,v1;
reg [31:0] cost0,cost1,util0,util1;
reg [15:0] fid0,fid1;
reg [2:0] hops0,hops1;
reg [1:0] slot0,slot1;
wire ready0,ready1,ready2,ready3,ready4;
wire done0,done1,done2,done3,done4;
wire [2:0] pid0,pid1,pid2,pid3,pid4;
wire [7:0] sid0,sid1,sid2,sid3,sid4;
wire [1:0] prof0,prof1,prof2,prof3,prof4;
wire [1:0] sel0,sel1,sel2,sel3,sel4;
wire [17:0] score0,score1,score2,score3,score4;
wire [15:0] bf0,bf1,bf2,bf3,bf4;
wire [2:0] status0,status1,status2,status3,status4;
wire [15:0] cyc0,cyc1,cyc2,cyc3,cyc4;
wire cv0,cv1,cv2,cv3,cv4;
integer errors,completions;

p5_b6_measurement_shell #(.POLICY_MODE(3'd0)) m0(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready0),.busy(),.done(done0),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid0),.state_id(sid0),.profile_id(prof0),.selected_slot(sel0),.selected_score(score0),
.bottleneck_fidelity(bf0),.status(status0),.cycles(cyc0),.cycles_valid(cv0));
p5_b6_measurement_shell #(.POLICY_MODE(3'd1)) m1(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready1),.busy(),.done(done1),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid1),.state_id(sid1),.profile_id(prof1),.selected_slot(sel1),.selected_score(score1),
.bottleneck_fidelity(bf1),.status(status1),.cycles(cyc1),.cycles_valid(cv1));
p5_b6_measurement_shell #(.POLICY_MODE(3'd2)) m2(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready2),.busy(),.done(done2),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid2),.state_id(sid2),.profile_id(prof2),.selected_slot(sel2),.selected_score(score2),
.bottleneck_fidelity(bf2),.status(status2),.cycles(cyc2),.cycles_valid(cv2));
p5_b6_measurement_shell #(.POLICY_MODE(3'd3)) m3(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready3),.busy(),.done(done3),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid3),.state_id(sid3),.profile_id(prof3),.selected_slot(sel3),.selected_score(score3),
.bottleneck_fidelity(bf3),.status(status3),.cycles(cyc3),.cycles_valid(cv3));
p5_b6_measurement_shell #(.POLICY_MODE(3'd4)) m4(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready4),.busy(),.done(done4),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid4),.state_id(sid4),.profile_id(prof4),.selected_slot(sel4),.selected_score(score4),
.bottleneck_fidelity(bf4),.status(status4),.cycles(cyc4),.cycles_valid(cv4));

always #5 clk=~clk;

task reset_all;
begin
 rst=1;start=0;input_valid=1;
 repeat(4) @(posedge clk);
 rst=0;
 repeat(2) @(posedge clk);
end
endtask

task run_case;
input integer tid;
input iv;
input [15:0] a,b,c,d;
input x0;
input [31:0] e;
input [15:0] f;
input [31:0] g;
input [2:0] h;
input [1:0] i;
input x1;
input [31:0] j;
input [15:0] k;
input [31:0] l;
input [2:0] m;
input [1:0] n;
integer guard;
reg s0,s1,s2,s3,s4;
begin
 input_valid=iv;min_key=a;state_fid=b;load=c;imbalance=d;
 v0=x0;cost0=e;fid0=f;util0=g;hops0=h;slot0=i;
 v1=x1;cost1=j;fid1=k;util1=l;hops1=m;slot1=n;
 while(!(ready0&&ready1&&ready2&&ready3&&ready4)) @(posedge clk);
 @(negedge clk);start=1;
 @(posedge clk);#1;
 @(negedge clk);start=0;
 s0=0;s1=0;s2=0;s3=0;s4=0;guard=0;
 while(!(s0&&s1&&s2&&s3&&s4)&&guard<5000) begin
   @(posedge clk);#1;guard=guard+1;
   if(cv0!==done0||cv1!==done1||cv2!==done2||cv3!==done3||cv4!==done4) errors=errors+1;
   if(done0&&!s0) begin s0=1;completions=completions+1;
     $display("QF6S,1,%0d,0,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status0==2?0:sid0,status0==2?0:prof0,status0==0?sel0:255,
      status0==0?score0:0,status0==0?bf0:0,cyc0,status0); end
   if(done1&&!s1) begin s1=1;completions=completions+1;
     $display("QF6S,1,%0d,1,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status1==2?0:sid1,status1==2?0:prof1,status1==0?sel1:255,
      status1==0?score1:0,status1==0?bf1:0,cyc1,status1); end
   if(done2&&!s2) begin s2=1;completions=completions+1;
     $display("QF6S,1,%0d,2,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status2==2?0:sid2,status2==2?0:prof2,status2==0?sel2:255,
      status2==0?score2:0,status2==0?bf2:0,cyc2,status2); end
   if(done3&&!s3) begin s3=1;completions=completions+1;
     $display("QF6S,1,%0d,3,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status3==2?0:sid3,status3==2?0:prof3,status3==0?sel3:255,
      status3==0?score3:0,status3==0?bf3:0,cyc3,status3); end
   if(done4&&!s4) begin s4=1;completions=completions+1;
     $display("QF6S,1,%0d,4,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status4==2?0:sid4,status4==2?0:prof4,status4==0?sel4:255,
      status4==0?score4:0,status4==0?bf4:0,cyc4,status4); end
 end
 if(!(s0&&s1&&s2&&s3&&s4)) begin
   $display("P6_RTL_REPLAY=FAIL_TIMEOUT_%0d",tid);$finish;
 end
 @(posedge clk);#1;
 input_valid=1;
end
endtask

initial begin
 clk=0;rst=1;start=0;input_valid=1;
 min_key=0;state_fid=0;load=0;imbalance=0;
 v0=0;v1=0;cost0=0;cost1=0;fid0=0;fid1=0;util0=0;util1=0;
 hops0=0;hops1=0;slot0=0;slot1=1;errors=0;completions=0;
'''
    lines=[head]
    for r in replay:
        tid=int(r["test_id"])
        if tid in RESET_IDS:
            lines.append(" reset_all;\n")
        vals=[tid,int(r["input_valid"]),int(r["min_key_occupancy_u16"]),
          int(r["bottleneck_fidelity_state_u16"]),int(r["offered_request_load_u16"]),
          int(r["utilization_imbalance_state_u16"]),int(r["c0_valid"]),
          int(r["c0_cost"]),int(r["c0_fidelity"]),int(r["c0_utilization"]),
          int(r["c0_hops"]),int(r["c0_slot"]),int(r["c1_valid"]),int(r["c1_cost"]),
          int(r["c1_fidelity"]),int(r["c1_utilization"]),int(r["c1_hops"]),int(r["c1_slot"])]
        lines.append(" run_case("+",".join(str(x) for x in vals)+");\n")
    lines.append(r'''
 if(errors==0&&completions==420)
   $display("P6_RTL_REPLAY=420_OF_420_COMPLETIONS_PASS");
 else
   $display("P6_RTL_REPLAY=FAIL completions=%0d errors=%0d",completions,errors);
 #20;$finish;
end
initial begin
 #100000000;$display("P6_RTL_REPLAY=FAIL_GLOBAL_TIMEOUT");$finish;
end
endmodule
''')
    TB.write_text("".join(lines),encoding="utf-8")

def run_rtl():
    with tempfile.TemporaryDirectory(prefix="qflow-p6-rtl-") as td:
        exe=Path(td)/"p6.vvp"
        sources=[
          ROOT/"rtl/rl/rl_state_encoder.v",
          ROOT/"rtl/rl/rl_policy_rom.v",
          ROOT/"rtl/rl/rl_profile_rom.v",
          ROOT/"rtl/rl/rl_controller.v",
          ROOT/"rtl/spartan6/p5_b4_candidate_evaluator.v",
          ROOT/"rtl/spartan6/p5_b5_policy_shell.v",
          ROOT/"rtl/spartan6/p5_b6_measurement_shell.v",
          TB]
        cmd=["iverilog","-g2005","-Wall","-Wimplicit","-s","tb_p6_full_replay",
             "-o",str(exe)]+[str(x) for x in sources]
        c=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(c.stdout,end="")
        require(c.returncode==0,"iverilog_compile")
        r=subprocess.run(["vvp",str(exe)],cwd=ROOT,text=True,
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        SIMLOG.write_text(r.stdout,encoding="utf-8")
        print(r.stdout,end="")
        require(r.returncode==0,"vvp_run")
        require("P6_RTL_REPLAY=420_OF_420_COMPLETIONS_PASS" in r.stdout,
                "rtl_completion_sentinel")
        require("P6_RTL_REPLAY=FAIL" not in r.stdout,"rtl_no_failure_marker")
        rows=[]
        for line in r.stdout.splitlines():
            if not line.startswith("QF6S,"):
                continue
            p=line.split(",")
            require(len(p)==11,"rtl_record_fields")
            rows.append(dict(zip(FIELDS,map(int,p[2:]))))
        require(len(rows)==420,"rtl_rows_420")
        require(len({(x["test_id"],x["policy_id"]) for x in rows})==420,
                "rtl_unique_keys")
        return sorted(rows,key=lambda x:(x["test_id"],x["policy_id"]))

def check_p5_cycle_model(golden):
    expected={(int(x["case_id"]),int(x["policy_mode"][1])):int(x["kernel_cycles"])
              for x in read_csv(P5_CYCLES)}
    got={(x["test_id"],x["policy_id"]):x["cycles"]
         for x in golden if x["test_id"]<20}
    require(expected==got,"cycle_model_matches_p5_100_rows")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    SIMLOG.parent.mkdir(parents=True,exist_ok=True)
    require(sha(REPLAY)=="83081e4eb165b887dfdd2c07bd467804f39b78e54e7a9026b4d96007091b07e7",
            "replay_hash")
    replay=read_csv(REPLAY)
    require(len(replay)==84,"replay_rows_84")
    policy=[int(x.strip(),16)&3 for x in POLICY.read_text().splitlines() if x.strip()]
    profiles=[int(x.strip(),16) for x in PROFILE.read_text().splitlines() if x.strip()]
    require(len(policy)==256,"policy_entries_256")
    require(len(profiles)==4,"profile_entries_4")
    reset_rows=[
      {"test_id":0,"reset_reason":"tier_a_contract_start"},
      {"test_id":5,"reset_reason":"p5_h3_contract_group"},
      {"test_id":10,"reset_reason":"p5_h4_dwell_contract_group"},
      {"test_id":1000,"reset_reason":"tier_b_heldout_start"}]
    write_csv(RESET_SPEC,["test_id","reset_reason"],reset_rows)
    golden=golden_rows(replay,policy,profiles)
    require(len(golden)==420,"golden_rows_420")
    check_p5_cycle_model(golden)
    write_csv(GOLDEN,FIELDS,golden)
    generate_tb(replay)
    rtl=run_rtl()
    write_csv(RTLCSV,FIELDS,rtl)
    mismatches=[]
    for g,r in zip(golden,rtl):
        if g!=r:
            mismatches.append((g,r))
    with COMPARELOG.open("w",encoding="utf-8") as f:
        f.write(f"GOLDEN_ROWS={len(golden)}\nRTL_ROWS={len(rtl)}\nMISMATCHES={len(mismatches)}\n")
        for g,r in mismatches[:50]:
            f.write("GOLDEN="+json.dumps(g,sort_keys=True)+"\n")
            f.write("RTL="+json.dumps(r,sort_keys=True)+"\n")
    require(not mismatches,"golden_rtl_exact_420")
    summary=[]
    for mode in range(5):
        rows=[x for x in rtl if x["policy_id"]==mode]
        statuses=Counter(x["status"] for x in rows)
        cycles=[x["cycles"] for x in rows]
        profiles_used=Counter(x["profile_id"] for x in rows if x["status"]!=2)
        summary.append({
          "policy_id":mode,"policy_name":f"H{mode}","rows":len(rows),
          "exact_matches":len(rows),"ok_rows":statuses[0],
          "no_path_rows":statuses[1],"invalid_rows":statuses[2],
          "min_cycles":min(cycles),"max_cycles":max(cycles),
          "mean_cycles":f"{sum(cycles)/len(cycles):.6f}",
          "profile0":profiles_used[0],"profile1":profiles_used[1],
          "profile2":profiles_used[2],"profile3":profiles_used[3]})
    write_csv(SUMMARY,[
      "policy_id","policy_name","rows","exact_matches","ok_rows","no_path_rows",
      "invalid_rows","min_cycles","max_cycles","mean_cycles",
      "profile0","profile1","profile2","profile3"],summary)
    print("P6_STEP3C_GOLDEN_ROWS=420_OF_420_PASS")
    print("P6_STEP3C_RTL_ROWS=420_OF_420_PASS")
    print("P6_STEP3C_EXACT_MATCHES=420_OF_420_PASS")
    print("P6_STEP3C_P5_CYCLE_MODEL=100_OF_100_PASS")
    print("P6_STEP3C_RESET_BOUNDARIES=4_OF_4_PASS")
    print("P6_STEP3C_GOLDEN_RTL=PASS")

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("P6_STEP3C_GOLDEN_RTL=FAIL:",e,file=sys.stderr)
        raise
