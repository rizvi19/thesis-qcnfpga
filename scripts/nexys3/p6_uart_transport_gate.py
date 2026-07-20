#!/usr/bin/env python3
from __future__ import annotations
import csv
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RTL=ROOT/"results/nexys3/p6_step3_golden_rtl/rtl_results.csv"
UART=ROOT/"rtl/spartan6/p5_b1_uart_tx.v"
TB=ROOT/"sim/spartan6/tb_p6_uart_byte_stream.v"
OUT=ROOT/"results/nexys3/p6_step3_uart_transport"
RAW=OUT/"simulated_raw_qf6r.log"
PARSED=OUT/"simulated_board_results.csv"
SUMMARY=OUT/"transport_summary.csv"
MEM=OUT/"expected_bytes.mem"
SIMLOG=ROOT/"evidence/nexys3/p6_step3_uart_transport/uart_bit_level_simulation.log"
COMPARE=ROOT/"evidence/nexys3/p6_step3_uart_transport/parser_exact_comparison.log"
PARSER=ROOT/"scripts/nexys3/parse_p6_qf6r.py"

FIELDS=["test_id","policy_id","state_id","profile_id","selected_path","score",
        "bottleneck_fidelity","cycles","status"]
WIDTHS={"test_id":4,"policy_id":1,"state_id":3,"profile_id":1,
        "selected_path":3,"score":6,"bottleneck_fidelity":5,
        "cycles":3,"status":1}

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def read_csv(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path,fields,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def require(c,label):
    if not c:
        raise AssertionError(label)
    print("PASS",label)

def make_record(row):
    vals=[f'{int(row[k]):0{WIDTHS[k]}d}' for k in FIELDS]
    line=("QF6R,1,"+",".join(vals)+"\r\n").encode("ascii")
    require(len(line)==44,"record_length_44")
    return line

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    SIMLOG.parent.mkdir(parents=True,exist_ok=True)

    rows=read_csv(RTL)
    require(len(rows)==420,"source_rows_420")
    require(len({(r["test_id"],r["policy_id"]) for r in rows})==420,
            "source_unique_keys")

    expected_raw=b"".join(make_record(r) for r in rows)
    require(len(expected_raw)==18480,"expected_bytes_18480")
    with MEM.open("w",encoding="ascii",newline="\n") as f:
        for b in expected_raw:
            f.write(f"{b:02X}\n")

    with tempfile.TemporaryDirectory(prefix="qflow-p6-uart-") as td:
        exe=Path(td)/"uart.vvp"
        cmd=["iverilog","-g2005","-Wall","-Wimplicit",
             "-s","tb_p6_uart_byte_stream","-o",str(exe),
             str(UART),str(TB)]
        c=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
        require(c.returncode==0,"iverilog_compile")
        r=subprocess.run(["vvp",str(exe)],cwd=ROOT,
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        SIMLOG.write_bytes(c.stdout+r.stdout)
        text=(c.stdout+r.stdout).decode("ascii","replace")
        print(text,end="")
        require(r.returncode==0,"vvp_run")
        require("P6_UART_BIT_LEVEL=18480_OF_18480_BYTES_PASS" in text,
                "uart_byte_sentinel")
        require("P6_UART_BIT_LEVEL=FAIL" not in text,
                "uart_no_failure_marker")
        pattern=re.compile(
          rb"QF6R,1,\d{4},\d,\d{3},\d,\d{3},\d{6},\d{5},\d{3},\d\r\n")
        matches=pattern.findall(r.stdout)
        require(len(matches)==420,"simulated_raw_records_420")
        raw=b"".join(matches)
        require(raw==expected_raw,"simulated_raw_exact_bytes")
        RAW.write_bytes(raw)

    p=subprocess.run(
      ["python3",str(PARSER),str(RAW),str(PARSED),
       "--expected-records","420"],
      cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    print(p.stdout,end="")
    require(p.returncode==0,"parser_run")

    parsed=read_csv(PARSED)
    expected=[{k:str(int(r[k])) for k in FIELDS} for r in rows]
    require(parsed==expected,"parser_exact_420")

    COMPARE.write_text(
      "SOURCE_ROWS=420\nRAW_RECORDS=420\nRAW_BYTES=18480\n"
      "PARSED_ROWS=420\nMISMATCHES=0\n",encoding="utf-8")

    prod_div=(100000000+115200//2)//115200
    actual=100000000/prod_div
    error=abs(actual-115200)/115200*100
    require(prod_div==868,"production_divisor_868")
    require(error<0.1,"production_baud_error_under_0_1_percent")

    write_csv(SUMMARY,["metric","value"],[
      {"metric":"records","value":420},
      {"metric":"bytes_per_record","value":44},
      {"metric":"serialized_bytes","value":18480},
      {"metric":"parsed_rows","value":420},
      {"metric":"mismatches","value":0},
      {"metric":"production_clock_hz","value":100000000},
      {"metric":"production_baud","value":115200},
      {"metric":"production_clks_per_bit","value":prod_div},
      {"metric":"production_actual_baud","value":f"{actual:.9f}"},
      {"metric":"production_baud_error_percent","value":f"{error:.9f}"}])

    print("P6_STEP3D_QF6R_RECORDS=420_OF_420_PASS")
    print("P6_STEP3D_UART_BYTES=18480_OF_18480_PASS")
    print("P6_STEP3D_PARSER_ROWS=420_OF_420_PASS")
    print("P6_STEP3D_EXACT_MATCHES=420_OF_420_PASS")
    print("P6_STEP3D_PRODUCTION_BAUD_GATE=PASS")
    print("P6_STEP3D_TRANSPORT_GATE=PASS")

if __name__=="__main__":
    main()
