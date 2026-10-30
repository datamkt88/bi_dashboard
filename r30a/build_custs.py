import json,re,csv,io,collections
from build_prows import load,D
TR='raw/'
import json as _j; _x=_j.load(open('r30a/custs_in.json')); act=_x['act']; cu=_x['cu']
print(len(act),len(cu),act[0],cu[0])
def regb(s):
    d,m,y=s.split(' ')[0].split('/'); y=int(y); m=int(m)
    return '<2025' if y<2025 else f'{y}-{m:02d}'
info={r[0]:(r[1],r[2],regb(r[3])) for r in cu}
mask=collections.defaultdict(int)
for j,c in act: mask[c]|=1<<int(j)
caffs=list(D['caffs']); ccurs=list(D['ccurs'])
grp=collections.Counter()
miss=collections.Counter()
for c,mk in mask.items():
    a,ci,rg=info[c]
    if a not in caffs: miss['aff']+=1; caffs.append(a)
    if ci not in ccurs: miss['cur']+=1; ccurs.append(ci)
    grp[(caffs.index(a),D['reg'].index(rg),mk,ccurs.index(ci))]+=1
new=[list(k) for k,n in grp.items() for _ in range(n)]
print('miss',miss,'new custs',len(new),'old',len(D['custs']))
# compare masks restricted to bits 0..11
old12=collections.Counter((a,r,m&0xFFF,c) for a,r,m,c in D['custs'] if m&0xFFF)
new12=collections.Counter((a,r,m&0xFFF,c) for a,r,m,c in new if m&0xFFF)
print('bits0-11 equal:', old12==new12, sum((old12-new12).values()), sum((new12-old12).values()))
for j in range(13):
    print(j, sum(1 for x in D['custs'] if x[2]>>j&1), sum(1 for x in new if x[2]>>j&1))
json.dump({'custs':new,'caffs':caffs,'ccurs':ccurs},open('custs_new.json','w'))
