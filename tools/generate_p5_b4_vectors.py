#!/usr/bin/env python3
import csv, random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'sim/spartan6'
MAX=0xFFFFFFFE
PROFILES=[(2,2,1),(1,1,2),(1,2,1),(2,1,1)]

def norm(v, lo, hi):
    if hi==lo: return 0
    return ((v-lo)*65535 + (hi-lo+1)//2)//(hi-lo+1)

def evaluate(a,b,lam):
    valid=[a['valid'],b['valid']]
    if not any(valid): return 1,0,0
    if sum(valid)==1:
        i=0 if valid[0] else 1
        return 0,(a,b)[i]['slot'],0
    vals=[(a['cost'],65535-a['fid'],a['util']),(b['cost'],65535-b['fid'],b['util'])]
    ns=[]
    for v in vals:
        ns.append(tuple(norm(v[j],min(vals[0][j],vals[1][j]),max(vals[0][j],vals[1][j])) for j in range(3)))
    scores=[max(lam[j]*ns[i][j] for j in range(3)) for i in range(2)]
    keys=[(scores[i],(a,b)[i]['cost'],(a,b)[i]['hops'],(a,b)[i]['slot']) for i in range(2)]
    w=0 if keys[0]<=keys[1] else 1
    return 0,(a,b)[w]['slot'],scores[w]

def pack(fields):
    x=0
    for value,width in fields: x=(x<<width)|(value&((1<<width)-1))
    return f'{x:050x}'

def cand(valid,cost,fid,util,hops,slot):
    return dict(valid=valid,cost=cost,fid=fid,util=util,hops=hops,slot=slot)

def main():
    rng=random.Random(0xB410)
    rows=[]
    directed=[
      (cand(0,0,0,0,0,0),cand(0,0,0,0,0,1),(2,2,1)),
      (cand(1,100,58982,65536,1,0),cand(0,0,0,0,0,1),(2,2,1)),
      (cand(0,0,0,0,0,0),cand(1,100,58982,65536,1,1),(1,1,2)),
      (cand(1,100,60000,10,2,0),cand(1,100,60000,10,2,1),(1,2,1)),
      (cand(1,101,60000,10,2,0),cand(1,100,60000,10,2,1),(2,1,1)),
      (cand(1,100,58982,10,2,0),cand(1,100,58983,10,2,1),(1,2,1)),
      (cand(1,100,65535,0,5,0),cand(1,MAX,58982,MAX,1,1),(2,2,1)),
    ]
    rows.extend(directed)
    while len(rows)<519:
        a=cand(rng.randrange(8)!=0,rng.randrange(0,MAX+1),rng.randrange(58982,65536),rng.randrange(0,MAX+1),rng.randrange(1,6),0)
        b=cand(rng.randrange(8)!=0,rng.randrange(0,MAX+1),rng.randrange(58982,65536),rng.randrange(0,MAX+1),rng.randrange(1,6),1)
        rows.append((a,b,PROFILES[rng.randrange(4)]))
    mem=[]; csvrows=[]
    for i,(a,b,lam) in enumerate(rows):
        no,slot,score=evaluate(a,b,lam)
        fields=[]
        for c in (a,b): fields += [(c['valid'],1),(c['cost'],32),(c['fid'],16),(c['util'],32),(c['hops'],3),(c['slot'],2)]
        fields += [(lam[0],2),(lam[1],2),(lam[2],2),(no,1),(slot,2),(score,18)]
        mem.append(pack(fields)); csvrows.append([i,*[a[k] for k in ('valid','cost','fid','util','hops','slot')],*[b[k] for k in ('valid','cost','fid','util','hops','slot')],*lam,no,slot,score])
    (OUT/'p5_b4_vectors.mem').write_text('\n'.join(mem)+'\n')
    with (OUT/'p5_b4_vectors.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['id','c0_valid','c0_cost','c0_fidelity','c0_utilization','c0_hops','c0_slot','c1_valid','c1_cost','c1_fidelity','c1_utilization','c1_hops','c1_slot','lambda0','lambda1','lambda2','no_path','selected_slot','selected_score']);w.writerows(csvrows)
    print('P5_B4_GENERATED_VECTORS=519')
if __name__=='__main__': main()
