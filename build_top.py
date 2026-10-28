from cand import *
import gzip,base64
days=PM['d']['days']; di={d:i for i,d in enumerate(days)}
def dkey(s):
    d,m,y=s.split(' ')[0].split('/'); return f'{y}-{int(m):02d}-{int(d):02d}'
S=json.load(open('pmseg.json')); sidx={tuple(s):i for i,s in enumerate(S['segs'])}
SEGOF=lambda c: sidx[tuple(x or '(None)' for x in MAP[c])] if c in MAP else None
# fix MAP blank handling same as build_seg
def segof(c):
    r=MAP[c]; k=(r[0] or '(Blank)', r[1] or '(Blank)', r[2] or '(None)', r[3] or '(None)'); return sidx[k]
# bonus
BM=collections.defaultdict(float); BD=collections.defaultdict(float)
for r in load(TR+'1791344842588.txt'):
    d=dkey(r[0]); BM[(d[:7],r[1])]+=float(r[2] or 0)
for r in [x for x in load(TR+'1791344851418.txt') if dkey(x[0])<'2026-09-28']+[x for x in load(TR+'1791785213554.txt') if dkey(x[0])<'2026-10-06']+load(TR+'1793163755268.txt'):
    d=dkey(r[0]); BD[(d,r[1])]+=float(r[2] or 0)
    if d[:7]>='2026-07': BM[(d[:7],r[1])]+=float(r[2] or 0)
def per(P):   # p -> cust -> [cell, wl, vb, mainprod, mainvb]
    O={}
    for p,pl in P.items():
        O[p]={}
        for c,(cell,pr) in pl.items():
            wl=sum(v[0] for v in pr.values()); vb=sum(v[1] for v in pr.values())
            mp,mv=max(pr.items(),key=lambda kv:(kv[1][1],abs(kv[1][0])))
            O[p][c]=[cell,-wl,vb,mp,mv[1]]   # -GGR = player net win
    return O
def topk(O,ps):
    G=collections.defaultdict(lambda:collections.defaultdict(float))
    for p in ps:
        for c,o in O.get(p,{}).items(): G[(o[0],segof(c))][c]+=o[1]
    ks=set()
    for g,d in G.items():
        l=[(v,c) for c,v in d.items()]
        for v,c in heapq.nlargest(N,l)+heapq.nsmallest(N,l): ks.add(c)
    return ks
def build(O,K,windows,bon,key):
    keep=set()
    for p in O:
        for c in topk(O,[p]): keep.add((p,c))
    for w in windows:
        for c in topk(O,w):
            for p in w:
                if c in O.get(p,{}): keep.add((p,c))
    rows=[]
    for p,c in keep:
        o=O[p][c]; cur=PM['cells'][o[0]][1]; cid=[x[2] for x in D['sc'] if x[1]==cur][0]
        f=fx[(K[p][:7])+'|'+cid]
        rows.append([p,int(c),round(o[1]*100),round(o[2]*100),o[3],round(o[4]*100),round(bon.get((key(p),c),0)*f*100)])
    return rows
M=json.load(open('pc_month.json')); OM={}
for ym,f in sorted(M.items()):
    mi=PM['m'].index(ym); P=cands(load(TR+f+'.txt'),lambda r,mi=mi:mi,0,lambda p:PM['m'][p]); OM.update(per(P))
nm=len(PM['m']); last=nm-1
win=[list(range(max(0,e-n+1),e+1)) for e in (last,last-1) for n in (3,6,12,nm)]
win+= [[i for i in range(nm) if PM['m'][i][:4]==PM['m'][e][:4]] for e in (last,last-1)]
RM=build(OM,PM['m'],win,BM,lambda p:PM['m'][p])
OD={}
for f in json.load(open('pc_day.json')):
    P=cands(load(TR+f+'.txt'),lambda r:di[dkey(r[0])],1,lambda p:days[p][:7]); OD.update(per(P))
nd=len(days); dl=nd-1
win=[list(range(max(0,e-n+1),e+1)) for e in (dl,dl-1) for n in (7,14,30,nd)]
win+=[[i for i in range(nd) if days[i][:7]==days[e][:7] and i<=e] for e in (dl,dl-1)]
RD=build(OD,days,win,BD,lambda p:days[p])
custs=sorted({r[1] for r in RM}|{r[1] for r in RD}); ci={c:i for i,c in enumerate(custs)}
cellOf={}
for O in (OM,OD):
    for p,d in O.items():
        for c,o in d.items(): cellOf[int(c)]=o[0]
def col(rows):
    rows=[[r[0],ci[r[1]]]+r[2:] for r in rows]; rows.sort()
    cols=[list(x) for x in zip(*rows)]
    for k in (0,1):
        pass
    p=cols[0]; cols[0]=[p[0]]+[p[i]-p[i-1] for i in range(1,len(p))]
    return cols
OUT={'cust':custs,'cell':[cellOf[c] for c in custs],'seg':[segof(str(c)) for c in custs],'m':col(RM),'d':col(RD)}
js=json.dumps(OUT,separators=(',',':')); b=base64.b64encode(gzip.compress(js.encode(),9)).decode()
open('pmtop.b64','w').write(b)
print('rows m',len(RM),'d',len(RD),'custs',len(custs),'b64',len(b))
# sanity: top winners Sep 2026 whole book
sep=PM['m'].index('2026-09'); t=sorted([r for r in RM if r[0]==sep],key=lambda r:-r[2])[:5]; print(t)
