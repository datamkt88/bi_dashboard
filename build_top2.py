import sys
sys.argv=['x']
exec(open('build_top.py').read().split("M=json.load(open('pc_month.json')); OM={}")[0])
def allrows(O,K,bon,key):
    rows=[]
    for p,d in O.items():
        for c,o in d.items():
            cur=PM['cells'][o[0]][1]; cid=[x[2] for x in D['sc'] if x[1]==cur][0]; f=fx[K[p][:7]+'|'+cid]
            rows.append([p,int(c),round(o[1]),round(o[2]),o[3],(round(o[4]/o[2]*100) if o[2]>0 else -1),round(bon.get((key(p),c),0)*f)])
    return rows
M=json.load(open('pc_month.json')); OM={}
for ym,f in sorted(M.items()):
    mi=PM['m'].index(ym); P=cands(load(TR+f+'.txt'),lambda r,mi=mi:mi,0,lambda p:PM['m'][p]); OM.update(per(P))
RM=allrows(OM,PM['m'],BM,lambda p:PM['m'][p])
OD={}
for f in json.load(open('pc_day.json')):
    rows=load(TR+f+'.txt')
    if f not in json.load(open('pc_new.json')): rows=[r for r in rows if dkey(r[0])<'2026-09-28']
    P=cands(rows,lambda r:di[dkey(r[0])],1,lambda p:days[p][:7]); OD.update(per(P))
RD=allrows(OD,days,BD,lambda p:days[p])
custs=sorted({r[1] for r in RM}|{r[1] for r in RD}); ci={c:i for i,c in enumerate(custs)}
cellOf={}
for O in (OM,OD):
    for p,d in O.items():
        for c,o in d.items(): cellOf[int(c)]=o[0]
def col(rows):
    rows=sorted([[r[0],ci[r[1]]]+r[2:] for r in rows])
    cols=[list(x) for x in zip(*rows)]
    p=cols[0]; cols[0]=[p[0]]+[p[i]-p[i-1] for i in range(1,len(p))]
    # cust index delta within period
    c=cols[1]; out=[c[0]]
    for i in range(1,len(c)): out.append(c[i]-c[i-1] if p[i]==p[i-1] else c[i])
    cols[1]=out
    return cols
cd=[custs[0]]+[custs[i]-custs[i-1] for i in range(1,len(custs))]
OUT={'cust':cd,'cell':[cellOf[c] for c in custs],'seg':[segof(str(c)) for c in custs],'m':col(RM),'d':col(RD)}
js=json.dumps(OUT,separators=(',',':')); b=base64.b64encode(gzip.compress(js.encode(),9)).decode()
open('pmtop.b64','w').write(b)
sep=PM['m'].index('2026-09'); xs=[r for r in RM if r[0]==sep]; print('sep players',len(xs),'top',sorted(xs,key=lambda r:-r[2])[:2],'bottom',sorted(xs,key=lambda r:r[2])[:2])
print('rows m',len(RM),'d',len(RD),'custs',len(custs),'b64',len(b))
