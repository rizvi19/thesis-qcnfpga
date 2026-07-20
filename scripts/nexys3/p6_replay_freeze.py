#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, random, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"results/nexys3/p6_replay"
A=OUT/"p6_contract_replay.csv"
B=OUT/"p6_heldout_dynamic_replay.csv"
ALL=OUT/"p6_all_replay.csv"
FREEZE=OUT/"p6_replay_freeze_v1.json"
SCHEMA=ROOT/"results/nexys3/p6_contract/replay_manifest_schema.csv"
SEED=26072026
FIELDS=["replay_order","test_id","replay_id","sequence_class","seed","src","dst",
"min_key_occupancy_u16","bottleneck_fidelity_state_u16","offered_request_load_u16",
"utilization_imbalance_state_u16","c0_valid","c0_cost","c0_fidelity","c0_utilization",
"c0_hops","c0_slot","c1_valid","c1_cost","c1_fidelity","c1_utilization","c1_hops",
"c1_slot","input_valid","expected_status","held_out"]
K=[0,16384,32768,49151]; F=[0,58982,60948,62914]
L=[0,16384,32768,49151]; I=[0,8192,16384,32768]

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def state_values(s):
    return K[(s>>6)&3],F[(s>>4)&3],L[(s>>2)&3],I[s&3]

def write(path,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n")
        w.writeheader(); w.writerows(rows)

def contract_rows():
    cases=[
      (0,0,1,1,0,"contract_single_c0"),(1,0,2,1,0,"contract_single_c1"),
      (2,0,3,1,0,"contract_dual_candidate"),(3,0,0,1,1,"contract_no_path"),
      (4,0,0,0,2,"contract_invalid"),(5,0,1,1,0,"h3_key_low"),
      (6,80,1,1,0,"h3_fidelity_low"),(7,98,1,1,0,"h3_imbalance_high"),
      (8,173,1,1,0,"h3_safe_saturated_load"),(9,164,1,1,0,"h3_default"),
      (10,0,1,1,0,"h4_dwell_start"),(11,25,1,1,0,"h4_dwell_hold_1"),
      (12,25,1,1,0,"h4_dwell_hold_2"),(13,25,1,1,0,"h4_dwell_switch_1"),
      (14,17,1,1,0,"h4_dwell_hold_3"),(15,17,1,1,0,"h4_dwell_hold_4"),
      (16,17,1,1,0,"h4_dwell_switch_2"),(17,104,1,1,0,"h4_dwell_hold_5"),
      (18,104,1,1,0,"h4_dwell_hold_6"),(19,104,1,1,0,"h4_dwell_switch_3")]
    out=[]
    for n,s,scenario,iv,status,label in cases:
        k,f,l,i=state_values(s)
        out.append(dict(replay_order=n,test_id=n,replay_id=f"A{n:03d}",
          sequence_class=label,seed=0,src=0,dst=3,
          min_key_occupancy_u16=k,bottleneck_fidelity_state_u16=f,
          offered_request_load_u16=l,utilization_imbalance_state_u16=i,
          c0_valid=int(scenario in (1,3)),c0_cost=100,c0_fidelity=62000,
          c0_utilization=10,c0_hops=3,c0_slot=0,
          c1_valid=int(scenario in (2,3)),c1_cost=200,c1_fidelity=62000,
          c1_utilization=10,c1_hops=2,c1_slot=1,input_valid=iv,
          expected_status=status,held_out=0))
    return out

def clip(v,lo=0,hi=65535): return max(lo,min(hi,v))
def near(r,c,d,lo=0,hi=65535): return clip(c+r.randint(-d,d),lo,hi)

def heldout_rows():
    r=random.Random(SEED); out=[]
    classes=["scarcity"]*16+["fidelity"]*16+["load_imbalance"]*16+["mixed"]*16
    no_path={7,23,39,55}; invalid={15,47}; only0={3,19,35,51}; only1={11,27,43,59}
    for n,cls in enumerate(classes):
        src=r.randrange(6); dst=r.randrange(5); dst += (dst>=src)
        h0=(dst-src)%6; h1=(src-dst)%6
        if cls=="scarcity":
            k=near(r,[4096,16000,17000,33000][n%4],1600); f=near(r,62000,1800)
            l=near(r,30000,10000); i=near(r,12000,9000)
        elif cls=="fidelity":
            k=near(r,36000,9000); f=near(r,[57500,59200,61100,63200][n%4],900)
            l=near(r,28000,12000); i=near(r,13000,10000)
        elif cls=="load_imbalance":
            k=near(r,39000,9000); f=near(r,62500,1800)
            l=near(r,[12000,20000,36000,52000][n%4],2200)
            i=near(r,[4000,10000,22000,40000][n%4],2200)
        else:
            k=r.randrange(65536); f=r.randrange(56000,65536)
            l=r.randrange(65536); i=r.randrange(50000)
        base=r.randrange(500,50000); delta=r.randrange(1,16000)
        c0cost=base
        c1cost=min(0xFFFFFFFE,base+delta if n%2==0 else max(1,base-delta//2))
        c0fid=max(58982,near(r,max(f,59000),1800))
        c1fid=max(58982,near(r,max(f,59000),1800))
        iv=0 if n in invalid else 1
        if n in no_path or n in invalid: v0=v1=0
        elif n in only0: v0,v1=1,0
        elif n in only1: v0,v1=0,1
        else: v0=v1=1
        status=2 if not iv else (1 if not(v0 or v1) else 0)
        out.append(dict(replay_order=20+n,test_id=1000+n,replay_id=f"B{n:03d}",
          sequence_class=cls,seed=SEED,src=src,dst=dst,
          min_key_occupancy_u16=k,bottleneck_fidelity_state_u16=f,
          offered_request_load_u16=l,utilization_imbalance_state_u16=i,
          c0_valid=v0,c0_cost=c0cost,c0_fidelity=c0fid,c0_utilization=r.randrange(1,80000),
          c0_hops=h0,c0_slot=0,c1_valid=v1,c1_cost=c1cost,c1_fidelity=c1fid,
          c1_utilization=r.randrange(1,80000),c1_hops=h1,c1_slot=1,
          input_valid=iv,expected_status=status,held_out=1))
    return out

def load(path):
    with path.open(encoding="utf-8",newline="") as f:
        rd=csv.DictReader(f); return list(rd.fieldnames or []),list(rd)

def require(c,label):
    if not c: raise AssertionError(label)
    print("PASS",label)

def generate():
    OUT.mkdir(parents=True,exist_ok=True)
    a=contract_rows(); b=heldout_rows(); allrows=a+b
    write(A,a); write(B,b); write(ALL,allrows)
    data={"schema_version":1,"phase":"P6","step":"P6_STEP_3B_REPLAY_FREEZE",
      "source_checkpoint":"224929c385e2199d551b7c692b6673cd695c7daa",
      "branch":"rl-nexys3-adaptive","contract_rows":20,"heldout_rows":64,
      "combined_rows":84,"heldout_seed":SEED,"heldout_tuning_after_hash":False,
      "replay_order":"A000_A019_then_B000_B063",
      "files":{str(A.relative_to(ROOT)):sha(A),str(B.relative_to(ROOT)):sha(B),
               str(ALL.relative_to(ROOT)):sha(ALL)},
      "generated_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
      "claim_boundary":{"replay_materialized_and_frozen":True,"golden_results":False,
        "rtl_simulation":False,"uart_capture":False,"physical_board_output":False}}
    FREEZE.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("P6_CONTRACT_REPLAY_ROWS=20")
    print("P6_HELDOUT_REPLAY_ROWS=64")
    print("P6_ALL_REPLAY_ROWS=84")
    print("P6_HELDOUT_SEED=26072026")
    print("P6_CONTRACT_REPLAY_SHA256="+sha(A))
    print("P6_HELDOUT_REPLAY_SHA256="+sha(B))
    print("P6_ALL_REPLAY_SHA256="+sha(ALL))
    print("P6_REPLAY_FREEZE_JSON_SHA256="+sha(FREEZE))
    print("P6_STEP3B_REPLAY_GENERATION=PASS")

def check():
    sh,_=load(SCHEMA); ah,a=load(A); bh,b=load(B); xh,x=load(ALL)
    require(sh==FIELDS,"step2_schema_header"); require(ah==FIELDS and bh==FIELDS and xh==FIELDS,"headers")
    require((len(a),len(b),len(x))==(20,64,84),"row_counts")
    require(x==a+b,"combined_exact")
    require([int(z["replay_order"]) for z in x]==list(range(84)),"replay_order")
    require([int(z["test_id"]) for z in a]==list(range(20)),"contract_ids")
    require([int(z["test_id"]) for z in b]==list(range(1000,1064)),"heldout_ids")
    require(len({z["replay_id"] for z in x})==84,"unique_replay_ids")
    require(all(int(z["seed"])==SEED and int(z["held_out"])==1 for z in b),"heldout_seed_flags")
    require(Counter(z["sequence_class"] for z in b)==Counter({"scarcity":16,"fidelity":16,"load_imbalance":16,"mixed":16}),"class_balance")
    require(Counter(int(z["expected_status"]) for z in b)==Counter({0:58,1:4,2:2}),"status_counts")
    for j,z in enumerate(x):
        src,dst=int(z["src"]),int(z["dst"])
        require(0<=src<6 and 0<=dst<6 and src!=dst,f"src_dst_{j}")
        require(int(z["c0_slot"])==0 and int(z["c1_slot"])==1,f"slots_{j}")
        iv=int(z["input_valid"]); anyc=int(z["c0_valid"]) or int(z["c1_valid"])
        exp=2 if not iv else (1 if not anyc else 0)
        require(int(z["expected_status"])==exp,f"status_{j}")
    f=json.loads(FREEZE.read_text())
    require(f["heldout_tuning_after_hash"] is False,"no_tuning_after_hash")
    for rel,digest in f["files"].items(): require(sha(ROOT/rel)==digest,"hash_"+rel)
    require(f["claim_boundary"]=={"replay_materialized_and_frozen":True,"golden_results":False,
      "rtl_simulation":False,"uart_capture":False,"physical_board_output":False},"claim_boundary")
    print("P6_STEP3B_REPLAY_VALIDATION=PASS")
    print("P6_STEP3B_REPLAY_ROWS=84_OF_84_PASS")
    print("P6_STEP3B_HELDOUT_CLASSES=4_OF_4_BALANCED")

if __name__=="__main__":
    try:
        generate() if "--generate" in sys.argv else check()
    except Exception as e:
        print("P6_STEP3B_REPLAY_VALIDATION=FAIL:",e,file=sys.stderr); raise
