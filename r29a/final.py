import json,re,gzip,base64,csv
H=open('B2C-Marketing.html',encoding='utf-8').read()
def setblk(id_,typ,content):
    global H
    m=re.search(r'<script id="%s" type="[^"]*"( data-enc="gz")?>(.*?)</script>'%id_,H,re.S); assert m,id_
    H=H[:m.start(2)]+content+H[m.end(2):]
def getgz(id_):
    m=re.search(r'<script id="%s" type="text/plain" data-enc="gz">(.*?)</script>'%id_,H,re.S)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))
b64=lambda o: base64.b64encode(gzip.compress((o if isinstance(o,str) else json.dumps(o,separators=(',',':'),ensure_ascii=False)).encode(),9)).decode()
# segment cubes (same encoding as asm_seg.py)
S=json.load(open('pmseg.json'))
def col(rows):
    n=len(rows[0]); out=[]
    for i in range(n):
        c=[r[i] for r in rows]
        if n-3<=i<n-1: c=[round(x*100) for x in c]
        if i==0: c=[c[0]]+[c[j]-c[j-1] for j in range(1,len(c))]
        out.append(c)
    return out
dvp={}
for r in S['d']['VP']: assert dvp.setdefault(r[4],r[3])==r[3]
C={t:{g:col(rows) for g,rows in S[t].items() if not (t=='d' and g=='VP')} for t in 'md'}
C['dvp']=[dvp.get(i,-1) for i in range(max(dvp)+1)]
mv={}
for r in S['m']['VP']: mv.setdefault(r[4],set()).add(r[3])
multi={k for k,v in mv.items() if len(v)>1}
C['m']['VP']=col([r for r in S['m']['VP'] if r[4] in multi])
C['mvp']=[(next(iter(mv[i])) if i in mv and i not in multi else -1) for i in range(max(mv)+1)]
print('multi',multi)
setblk('pmseg','',b64(C))
setblk('pmsegs','',json.dumps(S['segs'],separators=(',',':'),ensure_ascii=False).replace('</','<\\/'))
setblk('pmtop','',open('pmtop.b64').read())
# player analysis
V=getgz('vipdata'); N=json.load(open('r29a/vip2.json'))
for k in ['m','days','partial','dpartial','dlast','cells','RM','RD','FM','FD','ref','status','tags','list','asof']: V[k]=N[k]
rows=[r for r in csv.reader(open('r29a/base.csv'))][1:]
V['base']=[[r[0],r[1],int(r[2]),int(r[3]),int(r[4] or 0)] for r in rows if r]
print('players',sum(b[3] for b in V['base']),'list',len(V['list']))
setblk('vipdata','',b64(V))
open('B2C-Marketing.html','w',encoding='utf-8').write(H); print('bytes',len(H.encode()))
# marketing overview block
H=open('B2C-Marketing.html',encoding='utf-8').read()
m=re.search(r'<script id="mgdata" type="[^"]*"( data-enc="gz")?>(.*?)</script>',H,re.S); print('mg enc',m.group(1))
mg=open('r29a/mgdata.json').read()
new=b64(mg) if m.group(1) else mg.replace('</','<\\/')
H=H[:m.start(2)]+new+H[m.end(2):]
parts=re.split(r'(<script id="\w+" type="(?:application/json|text/plain)"[^>]*>.*?</script>)',H,flags=re.S)
R=[('28/10/2026 13:02','29/10/2026 10:22'),('28/10/2026 13:08','29/10/2026 10:30')]
n=0
for i in range(0,len(parts),2):
    for a,b in R:
        n+=parts[i].count(a); parts[i]=parts[i].replace(a,b)
H=''.join(parts); open('B2C-Marketing.html','w',encoding='utf-8').write(H); print('replaced',n,'bytes',len(H.encode()))
