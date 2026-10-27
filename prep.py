"""Glue steps between the raw Power BI pulls and the build scripts.
All raw pulls live in raw/<id>.txt (the JSON the dax_query tool saves; copy it there).

python3 prep.py csvs   RDIR          raw -> RDIR/*.csv for exec mkt aff T RM FM base RDoct l2 (ids from RDIR/ids.json)
python3 prep.py custs  RDIR          RDIR/custs_in.json  (state/custs_base.json + current-month actives from pc_oct)
python3 prep.py drows  RDIR          RDIR/drows_in.json  (NG = G1-BO-RB-PRO-ADJ)
python3 prep.py vipm   RDIR          vipm_fd.json / vipm_nr.json: keep rows before CUT, append new pulls
python3 prep.py miss   RDIR          RDIR/miss.txt = customers in pcM/pcD not in the segment map
python3 prep.py mapadd ID            append a _missmap result (raw/ID.txt) to map_extra2.csv
python3 prep.py pminsert RDIR        RDIR/pm.json -> <script id="pmdata"> in B2C-Marketing.html
python3 prep.py pcjson RDIR          point pc_month.json[current month] / pc_day.json / pc_new.json at this run's pulls
"""
import sys, json, csv, re, os
sys.argv_saved=sys.argv; sys.path.insert(0,'.')
def load(fn):
    import io
    j=json.load(open(fn)); t=''.join(x.get('text','') for x in j); t=t[t.index('] ')+2:]
    return list(csv.reader(io.StringIO(t)))
RAW=lambda i: f'raw/{i}.txt'
cmd=sys.argv[1]; arg=sys.argv[2] if len(sys.argv)>2 else None
CFG=json.load(open('state/config.json'))      # {"cut":"2026-10-06","month":"2026-10","month_bit":12}
def ids(r): return json.load(open(f'{r}/ids.json'))
def iso(s): d,m,y=s.split(' ')[0].split('/'); return f'{y}-{int(m):02d}-{int(d):02d}'
if cmd=='csvs':
    I=ids(arg)
    for name,drop in (('exec',None),('mkt',None),('aff',None),('T',None),('RM',None),('FM',None),('base',[3]),('RDoct',[5,6])):
        rows=[r for r in load(RAW(I[name])) if r]; h=rows[0]
        cut=len(h)-1 if h[-1]=='[pad]' else len(h)
        out=[h[:cut]]+[r[:cut] for r in rows[1:] if not (drop and all(r[i]=='' for i in drop))]
        csv.writer(open(f'{arg}/{name}.csv','w',newline='')).writerows(out); print(name,len(out)-1)
    rows=[r for r in load(RAW(I['l2'])) if r]
    csv.writer(open(f'{arg}/l2.csv','w',newline='')).writerows([r[:2] for r in rows]); print('l2',len(rows)-1)
elif cmd=='custs':
    I=ids(arg); base=json.load(open('state/custs_base.json')); bit=str(CFG['month_bit'])
    pc=[r for r in load(RAW(I['pc_oct']))[1:] if r]
    act=[a for a in base['act'] if a[0]!=bit]+[[bit,r[0]] for r in pc if float(r[6] or 0)>0]
    have={c[0] for c in base['cu']}; cu=base['cu']+[r[:4] for r in pc if r[0] not in have]
    json.dump({'act':act,'cu':cu},open(f'{arg}/custs_in.json','w')); print('act',len(act),'cu',len(cu))
elif cmd=='drows':
    I=ids(arg); f=lambda x: float(x) if x else 0.0
    rows=[r for r in load(RAW(I['drows']))[1:] if r]
    out=[r[:11]+[str(round(f(r[11])-f(r[12])-f(r[13])-f(r[14])-f(r[15]),6))] for r in rows]
    json.dump(out,open(f'{arg}/drows_in.json','w')); print('drows',len(out))
elif cmd=='vipm':
    I=ids(arg); cut=CFG['cut']
    fd=[r for r in json.load(open('vipm_fd.json')) if iso(r[1])<cut]; nr=[r for r in json.load(open('vipm_nr.json')) if iso(r[1])<cut]
    a=[r[:4] for r in load(RAW(I['vipm_fd']))[1:] if r]; b=[r[:2] for r in load(RAW(I['vipm_nr']))[1:] if r]
    json.dump(fd+a,open('vipm_fd.json','w')); json.dump(nr+b,open('vipm_nr.json','w')); print('vipm_fd',len(fd),'+',len(a),' vipm_nr',len(nr),'+',len(b))
elif cmd=='miss':
    I=ids(arg); MAP=set(r[0] for r in load(RAW('1791343166441'))[1:] if r)
    for fn in ('map_extra.csv','map_extra2.csv'): MAP|={l.split(',')[0] for l in open(fn) if l.strip()}
    seen=set()
    for i in [I['pcM']]+I['pcD']:
        rows=[r for r in load(RAW(i))[1:] if r]; k=0 if i==I['pcM'] else 1
        seen|={r[k] for r in rows}
    miss=sorted(seen-MAP); open(f'{arg}/miss.txt','w').write('\n'.join(miss))
    print('missing from segment map:',len(miss), '-> run queries/_missmap_TEMPLATE.dax with these ids, then prep.py mapadd <id>' if miss else '')
elif cmd=='mapadd':
    rows=[r for r in load(RAW(arg))[1:] if r]; have={l.split(',')[0] for l in open('map_extra2.csv') if l.strip()}
    new=[r[:5] for r in rows if r[0] not in have]
    with open('map_extra2.csv','a') as fh:
        for r in new: fh.write(','.join(r)+'\n')
    print('added',len(new))
elif cmd=='pminsert':
    H=open('B2C-Marketing.html',encoding='utf-8').read()
    m=re.search(r'<script id="pmdata" type="application/json">(.*?)</script>',H,re.S)
    pm=open(f'{arg}/pm.json').read().replace('</','<\\/')
    H=H[:m.start(1)]+pm+H[m.end(1):]; open('B2C-Marketing.html','w',encoding='utf-8').write(H); print('pmdata',len(pm))
elif cmd=='pcjson':
    I=ids(arg); M=json.load(open('pc_month.json')); M[CFG['month']]=I['pcM']; json.dump(M,open('pc_month.json','w'))
    hist=json.load(open('state/pc_day_hist.json'))      # chunks before CUT (fixed)
    json.dump(hist+I['pcD'],open('pc_day.json','w')); json.dump(['1791785152514']+I['pcD'],open('pc_new.json','w'))
    print('pc_month',CFG['month'],I['pcM'],' pc_day',len(hist)+len(I['pcD']))
else: print(__doc__)
