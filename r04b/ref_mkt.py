import json,re,collections,sys
sys.argv=['x']; sys.path.insert(0,'.')
from build_prows import load,build,D,P
TR='raw/'
I={c:i for i,c in enumerate(P)}
prev=build(load(TR+'91793590002471.txt'),'2026-10')     # final 2026-10 (fixed)
cur=build(load(TR+'91793769087644.txt'),'2026-11')
def rows_for(ym,cur,prevAct,acq):
    keys=set(cur)|{k for k,o in prevAct.items() if o['Act']>0}
    out=[]
    for k in sorted(keys):
        a,rg,ci=k; o=cur.get(k,collections.defaultdict(float))
        row=[ym,a,rg,ci]
        for c in P[4:]:
            if c=='UP': row.append(float(o.get('Act',0)))
            elif c=='PA': row.append(float(prevAct.get(k,{}).get('Act',0)))
            elif c=='Acq': row.append(acq.get(a,0))
            else:
                v=o.get(c,0); row.append(round(v,2) if isinstance(v,float) else float(v))
        out.append(row)
    return out
acq={r[1]:r[I['Acq']] for r in D['prows'] if r[0]=='2026-11'}
newN=rows_for('2026-11',cur,prev,acq)
old=[r for r in D['prows'] if r[0]=='2026-11']
print('2026-11','rows',len(old),'->',len(newN))
for c in ['NRU','FDU','Act','Dep','VB','GGR','PA','RT']:
    print('  ',c, round(sum(r[I[c]] for r in old),1), round(sum(r[I[c]] for r in newN),1))
print('2026-10 rows kept',sum(1 for r in D['prows'] if r[0]=='2026-10'))
json.dump({'cur':newN,'month':'2026-11'},open('r04b/prows_new.json','w'))
