import json,re,csv,io,collections,datetime,sys
sys.path.insert(0,'.')
from build_prows import load
TR='raw/'
Q='uploads/QueryResults/dax_query_result_20261027_'
H=open('B2C-Marketing.html',encoding='utf-8').read()
D=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',H,re.S).group(1))
X=json.loads(re.search(r'<script id="edaily" type="application/json">(.*?)</script>',H,re.S).group(1))
E={c:i for i,c in enumerate(D['ecols'])}
CUR={r[2]:r[1] for r in D['sc']}; fx=D['fx']
num=lambda x: float(x) if x else 0.0
def P(s):  # parse model datetime
    return datetime.datetime.strptime(s,'%d/%m/%Y %I:%M:%S %p') if s else None
months=[]; y,m=2025,9
while (y,m)<=(2026,10): months.append(f'{y}-{m:02d}'); y,m=(y+(m==12),m%12+1)
d0=datetime.date(2026,7,1); days=[(d0+datetime.timedelta(i)).isoformat() for i in range(122)]
MI={k:i for i,k in enumerate(months)}; DI={k:i for i,k in enumerate(days)}
CELL=[]; 
def cell(si,cur):
    k=[si,cur]
    if k not in CELL: CELL.append(k)
    return CELL.index(k)
# 1 exec totals
TOT={'m':collections.Counter(),'d':collections.Counter()}  # (i,cell,'nru'|'fdu')
for r in D['erows']:
    if r[0] in MI:
        c=cell(r[1],r[2]); TOT['m'][(MI[r[0]],c,'nru')]+=r[E['NRU']]; TOT['m'][(MI[r[0]],c,'fdu')]+=r[E['FDU']]
for r in X['rows']:
    if r[0] in DI:
        c=cell(r[1],r[2]); TOT['d'][(DI[r[0]],c,'nru')]+=r[E['NRU']]; TOT['d'][(DI[r[0]],c,'fdu')]+=r[E['FDU']]
# 2 L2+ map
L2={}
for r in list(csv.reader(open('r30b/l2.csv')))[1:]:
    if r: L2[r[0]]=int(r[1])
print('L2+ players',len(L2))
# 3 player list
pl=[r[:12] for r in load(TR+'91793336777084.txt')+load(TR+'91793336777118.txt')]; print('player rows',len(pl), pl[0][:4])
PL={r[0]:r for r in pl}
# FDU per customer (marketing)
fd=json.load(open('vipm_fd.json')); nr=json.load(open('vipm_nr.json')); print('fdu rows',len(fd),'nru rows',len(nr), fd[0], nr[0])
custcell={}
for r in fd: custcell[r[0]]=cell(r[2],CUR.get(r[3],r[3]))
for r in pl: custcell.setdefault(r[0],cell(r[2],CUR.get(r[3],r[3])))
LV=collections.Counter()
chkF=collections.Counter(); chkN=collections.Counter()
miss=0
for kind,rows in (('fdu',fd),('nru',nr)):
    for r in rows:
        dt=P(r[1]).date().isoformat(); mk=dt[:7]
        (chkF if kind=='fdu' else chkN)[mk]+=1
        v=L2.get(r[0],1)
        if v<2: continue
        c=custcell.get(r[0])
        if c is None: miss+=1; continue
        if mk in MI: LV[('m',MI[mk],c,v,kind)]+=1
        if dt in DI: LV[('d',DI[dt],c,v,kind)]+=1
print('L2+ without cell',miss)
for m in months:
    print(m,'FDU cust rows',chkF[m],'exec',sum(v for (i,c,k),v in TOT['m'].items() if i==MI[m] and k=='fdu'),'| NRU',chkN[m],sum(v for (i,c,k),v in TOT['m'].items() if i==MI[m] and k=='nru'))
json.dump({'CELL':CELL,'TOT':{g:[[*k,v] for k,v in TOT[g].items()] for g in TOT},'LV':[[*k,v] for k,v in LV.items()]},open('r30b/vip2_stage1.json','w'))
