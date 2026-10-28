import json,re,sys,collections
sys.path.insert(0,'.'); sys.argv=['x']
from build_prows import load
TR='raw/'
H=open('B2C-Marketing.html',encoding='utf-8').read()
D=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',H,re.S).group(1))
X=json.loads(re.search(r'<script id="edaily" type="application/json">(.*?)</script>',H,re.S).group(1))
fx=D['fx']; CUR={r[2]:r[1] for r in D['sc']}; E={c:i for i,c in enumerate(D['ecols'])}
def iso(s): d,m,y=s.split(' ')[0].split('/'); return f'{y}-{int(m):02d}-{int(d):02d}'
num=lambda x: float(x) if x else 0.0
cells=[];segs=[];ci={};si={}
def ix(lst,d,k):
    if k not in d: d[k]=len(lst); lst.append(list(k))
    return d[k]
# cols: NRU FDU Act Depr RD Dep FD W VB GGR NGGR BO
COLS=['NRU','FDU','Act','Depr','RD','Dep','FD','W','VB','GGR','NGGR','BO']
def conv(per,cur,v):
    f=fx[per[:7]+'|'+cur]
    NRU,FDU,Act,Depr,RD,Dep,FD,W,VB,WL,BO,RB,PRO,ADJ=[num(x) for x in v]
    g=-WL
    return [int(NRU),int(FDU),int(Act),int(Depr),int(RD)]+[round(x*f,2) for x in (Dep,FD,W,VB,g,g-BO-RB-PRO-ADJ,BO)]
out={'m':[],'d':[]}
months=sorted({r[0] for r in load(TR+'1793163785777.txt')})
for r in load(TR+'1793163785777.txt'):
    k,s,c=r[0],r[1],r[2]
    if c not in CUR: continue
    v=conv(k,c,r[6:20])
    if not any(v): continue
    out['m'].append([months.index(k),ix(cells,ci,(s,CUR[c])),ix(segs,si,(r[3] or '(Blank)',r[4] or '(Blank)',r[5] or '(Blank)'))]+v)
days=sorted({iso(r[0]) for r in load(TR+'1793163789491.txt')})
for r in load(TR+'1793163789491.txt'):
    d=iso(r[0]); s,c=r[1],r[2]
    if c not in CUR: continue
    v=conv(d,c,r[6:20])
    if not any(v): continue
    out['d'].append([days.index(d),ix(cells,ci,(s,CUR[c])),ix(segs,si,(r[3] or '(Blank)',r[4] or '(Blank)',r[5] or '(Blank)'))]+v)
# validate vs exec
def tot(rows,i,col): return sum(r[3+COLS.index(col)] for r in rows if r[0]==i)
bad=0
for i,m in enumerate(months):
    e=[r for r in D['erows'] if r[0]==m]
    for col,ec in (('NRU','NRU'),('FDU','FDU'),('Act','Act'),('Dep','D')):
        a=tot(out['m'],i,col); b=sum(r[E[ec]]*(fx[m+'|'+r[3]] if col=='Dep' else 1) for r in e)
        if abs(a-b)>max(1,abs(b)*1e-6): bad+=1; print('M',m,col,a,round(b,2))
for i,d in enumerate(days):
    e=[r for r in X['rows'] if r[0]==d]
    for col,ec in (('NRU','NRU'),('FDU','FDU'),('Act','Act')):
        a=tot(out['d'],i,col); b=sum(r[E[ec]] for r in e)
        if abs(a-b)>0.5: bad+=1; print('D',d,col,a,b)
print('mismatches',bad,'months',months[0],months[-1],'days',days[0],days[-1],len(days),'segs',len(segs),'rows',len(out['m']),len(out['d']))
MG={'cols':COLS,'m':months,'days':days,'cells':cells,'segs':segs,'M':out['m'],'D':out['d'],'partial':'2026-10','dlast':'2026-10-27','dpart':'2026-10-28'}
json.dump(MG,open('r28b/mgdata.json','w'),separators=(',',':'),ensure_ascii=False)
import os; print(os.path.getsize('r28b/mgdata.json'))
