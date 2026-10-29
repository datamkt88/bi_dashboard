import json,re,csv,io,collections,datetime,sys
sys.path.insert(0,'.')
from build_prows import load
TR='raw/'
Q='uploads/QueryResults/dax_query_result_20261027_'
H=open('B2C-Marketing.html',encoding='utf-8').read()
D=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',H,re.S).group(1))
S=json.load(open('r29a/vip2_stage1.json')); CELL=S['CELL']
CUR={r[2]:r[1] for r in D['sc']}; fx=D['fx']
num=lambda x: float(x) if x else 0.0
P=lambda s: datetime.datetime.strptime(s,'%d/%m/%Y %I:%M:%S %p') if s else None
months=[]; y,m=2025,9
while (y,m)<=(2026,10): months.append(f'{y}-{m:02d}'); y,m=(y+(m==12),m%12+1)
d0=datetime.date(2026,7,1); days=[(d0+datetime.timedelta(i)).isoformat() for i in range(121)]
MI={k:i for i,k in enumerate(months)}; DI={k:i for i,k in enumerate(days)}
def cell(si,cid):
    k=[si,CUR.get(cid,cid)]
    if k not in CELL: CELL.append(k)
    return CELL.index(k)
usd=lambda v,cid: v*fx.get('2026-10|'+cid,0)
R={'m':collections.defaultdict(lambda:[0,0,0]),'d':collections.defaultdict(lambda:[0,0,0])}   # nru, cf, f7
F={'m':collections.defaultdict(lambda:[0,0,0,0,0,0,0,0]),'d':collections.defaultdict(lambda:[0,0,0,0,0,0,0,0])}  # fdu,new,one,dep,nd,ggr,bo,vb
# tallied NRU/FDU: L2+ from per-customer marketing rows, L1 = exec total - L2+
lv=collections.Counter()
for g,i,c,v,kind,n in S['LV']: lv[(g,i,c,kind)]+=n; (R if kind=='nru' else F)[g][(i,c,v)][0]+=n
for g in ('m','d'):
    for i,c,kind,n in S['TOT'][g]:
        (R if kind=='nru' else F)[g][(i,c,1)][0]+=n-lv[(g,i,c,kind)]
# profile extras: monthly R (cf, f7) and F (new, one, $)
for r in list(csv.reader(open('r29a/RM.csv')))[1:]:
    if not r or r[0] not in MI: continue
    o=R['m'][(MI[r[0]],cell(r[1],r[2]),int(r[3]))]; o[1]+=int(num(r[5])); o[2]+=int(num(r[6]))
def addF(g,i,c,v,r):
    o=F[g][(i,c,v)]; o[1]+=int(num(r[5])); o[2]+=int(num(r[6]))
    o[3]+=usd(num(r[7]),r[2]); o[4]+=usd(num(r[8]),r[2]); o[5]-=usd(num(r[9]),r[2]); o[6]+=usd(num(r[10]),r[2]); o[7]+=usd(num(r[11]),r[2])
for r in list(csv.reader(open('r29a/FM.csv')))[1:]:
    if r and r[0] in MI: addF('m',MI[r[0]],cell(r[1],r[2]),int(r[3]),r)
for r in load(TR+'1793241239918.txt'):
    if r[0] in DI: addF('d',DI[r[0]],cell(r[1],r[2]),int(r[3]),r)
# player list
pl=load(TR+'1793241004413.txt')+load(TR+'1793241056728.txt')
EP=datetime.date(2015,1,1)
dn=lambda d: (d.date()-EP).days if d else -1
ST=[]; TG=[]
def si(lst,x):
    x=x or '(Blank)'
    if x not in lst: lst.append(x)
    return lst.index(x)
tags=collections.defaultdict(list)
for c,t in load(TR+'1793241081912.txt'): tags[c].append(t)
badsb=0; LIST=[]; LN={}
lvnames=json.load(open('lvnames.json')) if False else None
for r in pl:
    c,sb,s,cid,rg,fd,lb,ld,v,st,dc,t=r[:12]
    rgd=P(rg); fdd=P(fd)
    if sb!=f'{s}_{c}': badsb+=1
    ce=cell(s,cid)
    row=[int(c),ce,dn(rgd),dn(fdd),dn(P(lb)),dn(P(ld)),int(v),si(ST,st),int(num(dc)),1 if t=='True' else 0,sorted(si(TG,x) for x in set(tags.get(c,[])))]+[ (lambda x: int(x) if x==int(x) else x)(round(num(z),2)) for z in r[12:16]]
    LIST.append(row)
    # daily R extras from the list (reg >= 1 Jul)
    if rgd and rgd.date().isoformat() in DI:
        o=R['d'][(DI[rgd.date().isoformat()],ce,int(v))]
        if fdd: o[1]+=1; o[2]+= 1 if fdd< rgd+datetime.timedelta(days=7) else 0
print('saba mismatch',badsb,'tags',len(TG),'status',ST)
def flat(dct): return [list(k)+[round(x,2) if isinstance(x,float) else x for x in v] for k,v in sorted(dct.items())]
OUT={'m':months,'days':days,'partial':'2026-10','dpartial':'2026-10-29','dlast':'2026-10-29','cells':CELL,
 'lv':{'1':'L1 · Vintage (Nova88) / Bronze','2':'L2 · Silver','3':'L3 · Gold','4':'L4 · Titanium','5':'L5 · Diamond','6':'L6 · VVVIP / Club'},
 'lvSite':{'Nova88':['VINTAGE CLUB','SILVER CLUB','GOLD CLUB','TITANIUM CLUB','DIAMOND CLUB','NOVA88 CLUB'],'Goal123':['BRONZE CLUB','SILVER CLUB','GOLD CLUB','TITANIUM CLUB','DIAMOND CLUB','GOAL123 CLUB'],'Bwing':['BRONZE CLUB','SILVER CLUB','GOLD CLUB','TITANIUM CLUB','DIAMOND CLUB','BWING VVVIP']},
 'RM':flat(R['m']),'RD':flat(R['d']),'FM':flat(F['m']),'FD':flat(F['d']),
 'ep':'2015-01-01','ref':'2026-10-29','status':ST,'tags':TG,'list':LIST,'asof':'2026-10-29 10:30'}
s=json.dumps(OUT,separators=(',',':')); open('r29a/vip2.json','w').write(s); print('bytes',len(s),'list',len(LIST))
# checks
for g,K in (('m',months),('d',days[-8:])):
    rows=OUT['RM' if g=='m' else 'RD']; fr=OUT['FM' if g=='m' else 'FD']
    for k in (K[-3:]):
        i=(months if g=='m' else days).index(k)
        print(g,k,'NRU',sum(r[3] for r in rows if r[0]==i),'FDU',sum(r[3] for r in fr if r[0]==i),'neg',[r for r in rows+fr if r[0]==i and r[3]<0][:3])
