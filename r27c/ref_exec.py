import json,re,csv
H=open('B2C-Marketing.html',encoding='utf-8').read()
D=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',H,re.S).group(1))
X=json.loads(re.search(r'<script id="edaily" type="application/json">(.*?)</script>',H,re.S).group(1))
ecols=D['ecols']; Q='uploads/QueryResults/dax_query_result_20261019_'
main=list(csv.reader(open('r27c/exec.csv'))); h=[x.strip('[]') for x in main[0]]
mk=list(csv.reader(open('r27c/mkt.csv'))); hm=[x.strip('[]') for x in mk[0]]
M={}
for r in mk[1:]:
    if r: o=dict(zip(hm,r)); M[(o['m'],o['Si'],o['Cu'])]=o
num=lambda x: float(x) if x not in ('',None) else 0.0
new={}
for r in main[1:]:
    if not r: continue
    o=dict(zip(h,r)); k=(o['m'],o['Si'],o['Cu']); row=[o['m'],o['Si'],o['Cu'],o['Ci']]
    for c in ecols[4:]:
        if c=='UP': row.append(num(o['Act']))
        elif c.startswith('Mkt'): row.append(num(M.get(k,{}).get(c)))
        else: row.append(num(o[c]))
    new.setdefault(o['m'],[]).append(row)
import collections
E={c:i for i,c in enumerate(ecols)}
allold={(r[0],r[1],r[2]):r for r in D['erows']+X['rows']}
for p in sorted(new):
    nd=0; mx=''
    for r in new[p]:
        o=allold.get((r[0],r[1],r[2]))
        for i in range(4,len(r)):
            ov=o[i] if o else 0
            if abs(r[i]-ov)>max(0.01,abs(ov)*1e-6): nd+=1; mx+=ecols[i]+' '
    print(p,'cells',len(new[p]),'diffs',nd, ' '.join(sorted(set(mx.split())))[:120])
P=[p for p in new if len(p)==7]; DS=[p for p in new if len(p)==10]
D['erows']=sorted([r for r in D['erows'] if r[0] not in P]+sum((new[p] for p in P),[]),key=lambda r:(r[0],r[1],r[2]))
X['rows']=sorted([r for r in X['rows'] if r[0] not in DS]+sum((new[d] for d in DS),[]),key=lambda r:(r[0],r[1],r[2]))
[X['days'].append(d) for d in sorted(DS) if d not in X['days']]; X['days'].sort()
X['partial']='2026-10-27'
json.dump({'erows':D['erows'],'edaily':X},open('exec_ref.json','w'))
E={c:i for i,c in enumerate(ecols)}
for d in DS: print(d,'NRU',sum(r[E['NRU']] for r in new[d]),'FDU',sum(r[E['FDU']] for r in new[d]))
print('Oct NRU',sum(r[E['NRU']] for r in new['2026-10']),'FDU',sum(r[E['FDU']] for r in new['2026-10']))
