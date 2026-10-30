import json,re,sys,collections; sys.argv=['x']; sys.path.insert(0,'.')
from build_prows import load
TR='raw/'
H=open('B2C-Marketing.html',encoding='utf-8').read()
def blk(n): return re.search(r'<script id="%s" type="application/json">(.*?)</script>'%n,H,re.S)
D=json.loads(blk('data').group(1)); fx=D['fx']; I={c:i for i,c in enumerate(D['pcols'])}
def iso(s): d,m,y=s.split(' ')[0].split('/'); return f'{y}-{int(m):02d}-{int(d):02d}'
num=lambda x: float(x) if x else 0.0
new=[]
for r in json.load(open('r30b/drows_in.json')):
    dt=iso(r[0]); f=fx[dt[:7]+'|'+r[2]]
    if r[2] not in D['dcurs']: D['dcurs'].append(r[2])
    NRU,FDU,Act,Tx,Dep,FD,W,VB,NG=[num(x) for x in r[3:]]
    new.append([dt,r[1],D['dcurs'].index(r[2]),int(NRU),int(FDU),int(Act),int(Tx),round(Dep*f,2),round(FD*f,2),round(W*f,2),round(VB*f,2),round(NG*f,2)])
keep=lambda r: any(r[i] for i in (3,4,5,6,7,9,10))
new=[r for r in new if keep(r)]
old={(r[0],r[1],r[2]):r for r in D['drows'] if r[0]>='2026-10-01'}
nk={(r[0],r[1],r[2]):r for r in new}
for d in sorted({k[0] for k in nk}):
    o=[k for k in old if k[0]==d]; n=[k for k in nk if k[0]==d]
    diff=sum(1 for k in set(o)|set(n) if k not in old or k not in nk or any(abs(old[k][c]-nk[k][c])>0.02 for c in range(3,12)))
    print(d,'old',len(o),'new',len(n),'row diffs',diff)
D['drows']=sorted([r for r in D['drows'] if r[0]<'2026-10-01']+new,key=lambda r:(r[0],r[1],r[2]))
# prows
ex=json.load(open('exec_ref.json')); D['erows']=ex['erows']
po=json.load(open('r30b/prows_new.json')); D['prows']=[r for r in D['prows'] if r[0] not in ('2026-09','2026-10')]+po['sep']+po['oct']
import csv
al=[r for r in list(csv.reader(open('r30b/aff.csv')))[1:] if r]
na=0; ch=0
for a,code,chn,src,mkt,site,pic,pf,own in al:
    v=[code,chn,src,mkt,site,pic,pf,own]
    if a not in D['aff']: na+=1
    elif D['aff'][a]!=v: ch+=1
    D['aff'][a]=v
for _a,_v in D['aff'].items():
    if _v[4]: D['asite'][_a]=_v[4]
print('master list',len(al),'new affs',na,'changed',ch)
rs=load(TR+'91793336777069.txt')
def ym(s): d,m,y=s.split(' ')[0].split('/'); return f'{y}-{int(m):02d}'
first=min(r[0] for r in D['srows'])
ns=sorted([[ym(r[0]),r[1],round(float(r[2] or 0),2),float(r[3] or 0),float(r[4] or 0),1] for r in rs if ym(r[0])>=first])
print('srows changed rows',len(set(map(tuple,ns))^set(map(tuple,D['srows']))))
D['srows']=ns; acq={(r[0],r[1]) for r in ns}; flips=0
for r in D['prows']:
    if r[0]>=first:
        v=1 if (r[0],r[1]) in acq else 0
        if r[I['Acq']]!=v: flips+=1; r[I['Acq']]=v
print('Acq flips',flips)
cu=json.load(open('custs_new.json')); D['custs']=cu['custs']; D['caffs']=cu['caffs']; D['ccurs']=cu['ccurs']
D['dlast']='2026-10-29'; D['factmax']='2026-10-30'; D['asof']='2026-10-30 13:06:00'
H=H[:blk('data').start(1)]+json.dumps(D,separators=(',',':'),ensure_ascii=False)+H[blk('data').end(1):]
H=H[:blk('edaily').start(1)]+json.dumps(ex['edaily'],separators=(',',':'))+H[blk('edaily').end(1):]
open('B2C-Marketing.html','w',encoding='utf-8').write(H)
print('drows',len(D['drows']))
