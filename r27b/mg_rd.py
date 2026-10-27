import json,re,csv,sys,collections
sys.path.insert(0,'.')
from build_prows import load
TR='raw/'
Q='uploads/QueryResults/dax_query_result_'
H=open('B2C-Marketing.html',encoding='utf-8').read()
D=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',H,re.S).group(1))
CUR={r[2]:r[1] for r in D['sc']}
MG=json.load(open('r27b/mgdata.json'))
iso=lambda s:(lambda d,m,y:f'{y}-{int(m):02d}-{int(d):02d}')(*s.split(' ')[0].split('/'))
B=lambda x:x or '(Blank)'
new={'m':{},'d':{}}
def put(g,per,s,c,a,b,t,depr,rd):
    if c not in CUR: return
    new[g][(per,s,CUR[c],B(a).lower(),B(b).lower(),B(t).lower())]=(int(float(depr or 0)),int(float(rd or 0)))
for r in load(TR+'1791883711575.txt'): put('m',r[0],*r[1:8])
for f,ym in (('20261013_172832_750','2026-07'),('20261013_172841_284','2026-08'),('20261013_172845_491','2026-09'),('r27b/RDoct','2026-10')):
    for r in list(csv.reader(open((f if f.startswith('r27b') else Q+f)+'.csv')))[1:]:
        if r: put('m',ym,*r[:7])
for r in load(TR+'1793075160368.txt'): put('d',iso(r[0]),*r[1:8])
RD=MG['cols'].index('RD')+3; DP=MG['cols'].index('Depr')+3
for g,rows,P in (('m',MG['M'],MG['m']),('d',MG['D'],MG['days'])):
    bad=miss=0; tot=collections.Counter(); old=collections.Counter()
    for r in rows:
        k=(P[r[0]],*MG['cells'][r[1]],*[x.lower() for x in MG['segs'][r[2]]])
        v=new[g].get(k)
        old[P[r[0]]]+=r[RD]
        if v is None: miss+=r[DP]>0; r[RD]=0; continue
        if v[0]!=r[DP]: bad+=1
        r[RD]=min(v[1],r[DP]); tot[P[r[0]]]+=r[RD]
    print(g,'rows',len(rows),'missing',miss,'Depr mismatch',bad)
    for p in P[-4:]: print('  ',p,'old RD',old[p],'new RD',tot[p], 'Depr',sum(r[DP] for r in rows if P[r[0]]==p))
json.dump(MG,open('r27b/mgdata.json','w'),separators=(',',':'),ensure_ascii=False)
