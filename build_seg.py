import json,re,collections,gzip,base64
from build_prows import load
TR='raw/'
H=open('B2C-Marketing.html',encoding='utf-8').read()
PM=json.loads(re.search(r'<script id="pmdata" type="application/json">(.*?)</script>',H,re.S).group(1))
D=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',H,re.S).group(1))
SITE={'1':'Nova88','2':'Goal123','3':'Bwing'}; CUR={r[2]:r[1] for r in D['sc']}; fx=D['fx']
cidx={tuple(c):i for i,c in enumerate(PM['cells'])}
pidx={p[0]:i for i,p in enumerate(PM['prods'])}; pcat=[p[1] for p in PM['prods']]
vidx={v:i for i,v in enumerate(PM['provs'])}
MAP={}
for r in load(TR+'1791343166441.txt'):
    MAP[r[0]]=(r[1] or '(Blank)', r[2] or '(Blank)', r[3] or '(None)', r[4] or '(None)')
for l in list(open('map_extra.csv'))+list(open('map_extra2.csv')):
    r=l.strip().split(','); MAP[r[0]]=(r[1] or '(Blank)', r[2] or '(Blank)', r[3] or '(None)', r[4] or '(None)')
segs=[]; sidx={}
def seg(c):
    k=MAP.get(c,('(Unknown)','(Unknown)','(None)','(None)'))
    if k not in sidx: sidx[k]=len(segs); segs.append(list(k))
    return sidx[k]
miss=collections.Counter()
def agg(rows, pfun, off):
    G={g:collections.defaultdict(lambda:[0.0,0.0,set()]) for g in 'T C P V VC VP'.split()}
    for r in rows:
        p,r=pfun(r),r[off:]
        if r[1] not in SITE or r[2] not in CUR: continue
        if r[3] not in vidx or r[4] not in pidx: miss[(r[3],r[4])]+=1; continue
        c=cidx[(SITE[r[1]],CUR[r[2]])]; f=fx[pk(p)+'|'+r[2]]; s=seg(r[0])
        pr=pidx[r[4]]; ca=pcat[pr]; v=vidx[r[3]]
        wl=-float(r[5] or 0)*f; vb=float(r[6] or 0)*f
        for g,k in (('T',(p,c,s)),('C',(p,c,s,ca)),('P',(p,c,s,pr)),('V',(p,c,s,v)),('VC',(p,c,s,v,ca)),('VP',(p,c,s,v,pr))):
            o=G[g][k]; o[0]+=wl; o[1]+=vb; o[2].add(r[0])
    return G
OUT={'m':{g:[] for g in 'T C P V VC VP'.split()},'d':{g:[] for g in 'T C P V VC VP'.split()}}
def emit(G,dst):
    for g,dd in G.items():
        for k,o in dd.items(): dst[g].append(list(k)+[round(o[0],2),round(o[1],2),len(o[2])])
M=json.load(open('pc_month.json'))
for ym,f in sorted(M.items()):
    mi=PM['m'].index(ym); pk=lambda p,ym=ym: ym
    emit(agg(load(TR+f+'.txt'),lambda r,mi=mi:mi,0),OUT['m'])
days=PM['d']['days']; di={d:i for i,d in enumerate(days)}
def dkey(s):
    d,m,y=s.split(' ')[0].split('/'); return f'{y}-{int(m):02d}-{int(d):02d}'
pk=lambda p: days[p][:7]
NEWD=set(json.load(open('pc_new.json')))
for f in json.load(open('pc_day.json')):
    rows=load(TR+f+'.txt')
    if f not in NEWD: rows=[r for r in rows if dkey(r[0])<'2026-09-28']
    emit(agg(rows,lambda r:di[dkey(r[0])],1),OUT['d'])
for a in OUT.values():
    for g in a: a[g].sort()
OUT['segs']=segs
print('miss',miss.most_common(5),'segs',len(segs))
for t in 'md':
    print(t,{g:len(v) for g,v in OUT[t].items() if g!='segs'})
# validate: sum over segs == PM arrays
def chk(src,mine,nk):
    A={tuple(r[:nk]):r[nk:] for r in src}; B=collections.defaultdict(lambda:[0,0,0])
    for r in mine:
        k=tuple(r[:2]+r[3:3+nk-2]); b=B[k]; b[0]+=r[-3]; b[1]+=r[-2]; b[2]+=r[-1]
    bad=[k for k in set(A)|set(B) if k not in A or k not in B or abs(A[k][0]-B[k][0])>1 or abs(A[k][1]-B[k][1])>1 or A[k][2]!=B[k][2]]
    return len(A),len(B),len(bad),[(k,A.get(k),B.get(k)) for k in bad[:3]]
for g,nk in (('T',2),('C',3),('P',3),('V',3),('VC',4),('VP',4)):
    print('m',g,chk(PM[g],OUT['m'][g],nk)); print('d',g,chk(PM['d'][g],OUT['d'][g],nk))
js=json.dumps(OUT,separators=(',',':'))
gz=gzip.compress(js.encode(),9)
print('raw',len(js),'gz',len(gz),'b64',len(base64.b64encode(gz)))
json.dump(OUT,open('pmseg.json','w'),separators=(',',':'))
