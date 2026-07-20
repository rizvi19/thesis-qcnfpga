#!/usr/bin/env python3
import subprocess, pathlib, shutil, sys
root=pathlib.Path(__file__).resolve().parents[2]
iv=shutil.which('iverilog'); vv=shutil.which('vvp')
if not iv or not vv: raise SystemExit('ERROR: install iverilog and vvp')
exe=root/'sim/spartan6/p5_b4_tb.vvp'
cmd=[iv,'-g2005','-o',str(exe),str(root/'rtl/spartan6/p5_b4_candidate_evaluator.v'),str(root/'sim/spartan6/tb_p5_b4_candidate_evaluator.v')]
subprocess.run(cmd,cwd=root,check=True)
r=subprocess.run([vv,str(exe)],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(r.stdout,end='')
if r.returncode or '519_OF_519_EXACT_PASS' not in r.stdout: raise SystemExit(1)
