import json,re,csv,sys
sys.path.insert(0,'.')
from build_prows import load
H=open('B2C-Marketing.html',encoding='utf-8').read()
D=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',H,re.S).group(1))
PM=json.loads(re.search(r'<script id="pmdata" type="application/json">(.*?)</script>',H,re.S).group(1))
SITE={'1':'Nova88','2':'Goal123','3':'Bwing'}; CUR={r[2]:r[1] for r in D['sc']}; fx=D['fx']
cidx={tuple(c):i for i,c in enumerate(PM['cells'])}; cats=PM['cats']; prods=[p[0] for p in PM['prods']]; provs=PM['provs']
TR='raw/'
def rd(f):
    if f.startswith('179'): return load(TR+f+'.txt')
    if f.endswith('.csv'): return [r for r in list(csv.reader(open(f)))[1:] if r]
    return [r for r in list(csv.reader(open('uploads/QueryResults/dax_query_result_'+f+'.csv')))[1:] if r]
F={'T':'r27b/T.csv','C':'1793074675797','P':'1793074686148','V':'1793074694134','VC':'1793074703211','VP':'1793074713899'}
lk={'T':[],'C':[cats],'P':[prods],'V':[provs],'VC':[provs,cats],'VP':[provs,prods]}
mi=PM['m'].index('2026-10'); si=PM['m'].index('2026-09'); X=PM['d']
import datetime as dt
DAYS=[str(dt.date(2026,10,1)+dt.timedelta(i)) for i in range(27)]
for d in DAYS:
    if d not in X['days']: X['days'].append(d)
X['days'].sort()
DI={d:X['days'].index(d) for d in DAYS}
miss=set(); cdOct=PM['cd']['m'].index('2026-10')
oldT={'m':{r[1]:r for r in PM['T'] if r[0]==mi},'s':{r[1]:r for r in PM['T'] if r[0]==si}}
for n,f in F.items():
    rs=rd(f); out={'m':[],'s':[],'d':[]}; cdr=[]
    for r in rs:
        g,s_,ci=r[0],r[1],r[2]
        if s_ not in SITE or ci not in CUR: continue
        c=cidx.get((SITE[s_],CUR[ci]))
        if c is None: miss.add(('cell',s_,ci)); continue
        keys=[]; bad=False
        for lst,v in zip(lk[n],r[3:-3]):
            if v not in lst: miss.add((n,v)); bad=True; break
            keys.append(lst.index(v))
        if bad: continue
        ym='2026-10'
        fr=fx[ym+'|'+ci]; w,v,p=r[-3:]
        vals=[round(-float(w or 0)*fr,2),round(float(v or 0)*fr,2),int(float(p or 0))]
        if g=='m': out['m'].append([mi,c]+keys+vals); cdr.append([cdOct,27,c]+keys+[vals[2]])
        elif g=='s': out['s'].append([si,c]+keys+vals)
        elif g.startswith('c'): cdr.append([cdOct,int(g[1:]),c]+keys+[vals[2]])
        else: out['d'].append([DI[g],c]+keys+vals)
    if n=='T':
        for k in ('m',):
            o=oldT[k]; nn={r[1]:r for r in out[k]}
            print(k,'GGR',round(sum(r[2] for r in o.values())),'->',round(sum(r[2] for r in nn.values())),'p',sum(r[4] for r in o.values()),'->',sum(r[4] for r in nn.values()))
        od={r[0]:r for r in X['T'] if r[0] in DI.values()}
        for d in DAYS:
            a=[r for r in X['T'] if r[0]==DI[d]]; b=[r for r in out['d'] if r[0]==DI[d]]
            print(d,'p',sum(r[4] for r in a),'->',sum(r[4] for r in b),'GGR',round(sum(r[2] for r in a)),'->',round(sum(r[2] for r in b)))
    PM[n]=sorted([r for r in PM[n] if r[0]!=mi]+out['m'])
    X[n]=sorted([r for r in X[n] if r[0] not in DI.values()]+out['d'])
    PM['cd'][n]=sorted([r for r in PM['cd'][n] if r[0]!=cdOct]+cdr)
print('miss',miss)
X['have']=sorted(set(X['have'])|set(DI.values())); X['partial']='2026-10-27'; PM['dlast']='2026-10-27'
pp={}
for src in (PM['VP'],X['VP']):
    for r in src: pp.setdefault(r[3],set()).add(r[2])
PM['prodProv']=[sorted(pp.get(i,[])) for i in range(len(prods))]
json.dump(PM,open('r27b/pm.json','w'),separators=(',',':'))
print('days',len(X['days']),X['days'][-1])
