import json,re,collections,sys
sys.argv=['x']; sys.path.insert(0,'.')
from build_prows import load,build,D,P
TR='raw/'
I={c:i for i,c in enumerate(P)}
sep=build(load(TR+'1791784745621.txt'),'2026-09')
octa=build(load(TR+'1793163748809.txt'),'2026-10')
def rows_for(ym,cur,prevAct,acq,oldPA=None):
    keys=set(cur)|({k for k,o in prevAct.items() if o['Act']>0} if prevAct is not None else set())
    out=[]
    for k in sorted(keys):
        a,rg,ci=k; o=cur.get(k,collections.defaultdict(float))
        pa=prevAct.get(k,{}).get('Act',0) if prevAct is not None else oldPA.get(k,0)
        row=[ym,a,rg,ci]
        for c in P[4:]:
            if c=='UP': row.append(float(o.get('Act',0)))
            elif c=='PA': row.append(float(pa))
            elif c=='Acq': row.append(acq.get(a,0))
            else:
                v=o.get(c,0); row.append(round(v,2) if isinstance(v,float) else float(v))
        out.append(row)
    return out
acqO={r[1]:r[I['Acq']] for r in D['prows'] if r[0]=='2026-10'}
acqS={r[1]:r[I['Acq']] for r in D['prows'] if r[0]=='2026-09'}
oldS={(r[1],r[2],r[3]):r for r in D['prows'] if r[0]=='2026-09'}
oldPA={k:r[I['PA']] for k,r in oldS.items()}
# Sep: keep keys that only had PA (prev-month actives) from old rows
newS=rows_for('2026-09',sep,None,acqS,oldPA)
nk={(r[1],r[2],r[3]) for r in newS}
for k,r in oldS.items():
    if k not in nk: newS.append(r)
newO=rows_for('2026-10',octa,sep,acqO)
for ym,old,new in (('2026-09',list(oldS.values()),newS),('2026-10',[r for r in D['prows'] if r[0]=='2026-10'],newO)):
    print(ym,'rows',len(old),'->',len(new))
    for c in ['NRU','FDU','Act','Dep','VB','GGR','PA','RT']:
        print('  ',c, round(sum(r[I[c]] for r in old),1), round(sum(r[I[c]] for r in new),1))
json.dump({'sep':newS,'oct':newO},open('r28b/prows_new.json','w'))
