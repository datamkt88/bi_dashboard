import json,re,collections,heapq,sys
from build_prows import load
TR='raw/'
H=open('B2C-Marketing.html',encoding='utf-8').read()
PM=json.loads(re.search(r'<script id="pmdata" type="application/json">(.*?)</script>',H,re.S).group(1))
D=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',H,re.S).group(1))
SITE={'1':'Nova88','2':'Goal123','3':'Bwing'}; CUR={r[2]:r[1] for r in D['sc']}; fx=D['fx']
cidx={tuple(c):i for i,c in enumerate(PM['cells'])}
pidx={p[0]:i for i,p in enumerate(PM['prods'])}; pcat=[p[1] for p in PM['prods']]
MAP={}
for r in load(TR+'1791343166441.txt'): MAP[r[0]]=(r[1],r[2],r[3],r[4])
for l in list(open('map_extra.csv'))+list(open('map_extra2.csv')):
    r=l.strip().split(','); MAP[r[0]]=tuple(r[1:5])
N=10
def cands(rows,pf,off,ym_of):
    # per period: player -> {cell, wl by prod, vb by prod}
    P=collections.defaultdict(lambda: collections.defaultdict(lambda:[None,collections.defaultdict(lambda:[0.0,0.0])]))
    for r in rows:
        p=pf(r); r=r[off:]
        if r[1] not in SITE or r[2] not in CUR: continue
        f=fx[ym_of(p)+'|'+r[2]]; o=P[p][r[0]]; o[0]=cidx[(SITE[r[1]],CUR[r[2]])]
        x=o[1][pidx[r[4]]]; x[0]+=-float(r[5] or 0)*f; x[1]+=float(r[6] or 0)*f
    return P
def keep(P,lvl):
    ks=set()
    for p,pl in P.items():
        G=collections.defaultdict(list)
        for c,(cell,pr) in pl.items():
            seg=MAP.get(c)
            if lvl=='all': G[(cell,seg)].append((sum(v[0] for v in pr.values()),c))
            elif lvl=='cat':
                cc=collections.defaultdict(float)
                for k,v in pr.items(): cc[pcat[k]]+=v[0]
                for k,v in cc.items(): G[(cell,seg,'c',k)].append((v,c))
            else:
                for k,v in pr.items(): G[(cell,seg,'p',k)].append((v[0],c))
        for g,l in G.items():
            for v,c in heapq.nlargest(N,l)+heapq.nsmallest(N,l): ks.add((p,c))
    return ks
if __name__=='__main__':
    M=json.load(open('pc_month.json')); tot=collections.Counter()
    for ym,f in sorted(M.items()):
        P=cands(load(TR+f+'.txt'),lambda r,ym=ym:ym,0,lambda p:p)
        for lvl in ('all','cat','prod'): tot[lvl]+=len(keep(P,lvl))
        tot['players']+=len(P[ym])
    print(tot)
