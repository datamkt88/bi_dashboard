"""First run folder of a new month, made from the old month's last folder (after rollover.py).

python3 mkmonth.py r31 r02a ids_r02a.json

newrun.py refuses to cross a month; this does the crossing once. Later runs of the new month use newrun.py.
It copies <prev>/*.py, swaps pull ids and folder names, moves every month/day constant to the new month,
and rewrites ref_mkt.py (new month vs the final old month) and the mk.py prows line.
Every replacement is asserted, so a script layout change stops it instead of building something wrong.
"""
import sys, json, shutil, os, glob, re, datetime as dt
prev, new, idsf = sys.argv[1:4]
A = json.load(open(f'{prev}/ids.json')); B = json.load(open(idsf))
da, db = dt.date.fromisoformat(A['date']), dt.date.fromisoformat(B['date'])
O, N = da.strftime('%Y-%m'), db.strftime('%Y-%m'); assert O != N
P = (da.replace(day=1) - dt.timedelta(1)).strftime('%Y-%m')
R = json.load(open(f'state/rollover_{N}.json')); assert R['folder'] == prev
if os.path.exists(new): shutil.rmtree(new)
os.makedirs(new)
for f in glob.glob(f'{prev}/*.py'): shutil.copy(f, new)
json.dump(B, open(f'{new}/ids.json', 'w'), indent=1)
day0 = dt.date(2026, 7, 1); M0 = db.replace(day=1)
yN, mN = db.year, db.month
_k = yN * 12 + (mN - 1) - 13; y0, m0 = _k // 12, _k % 12 + 1      # 14-month window start (13 months back)
iO = lambda s: s.replace('{O}', O).replace('{N}', N).replace('{P}', P)
def edit(fn, pairs):
    p = f'{new}/{fn}'; s = open(p).read()
    for a, b in pairs:
        n = s.count(a); assert n, f'{fn}: not found: {a[:80]}'
        s = s.replace(a, b); print(f'{fn:16s} {n}x {a[:70]!r} -> {b[:70]!r}')
    open(p, 'w').write(s)
# ids (except the ones that must keep pointing at the old month's final pulls)
ids = [(A[k], B[k]) for k in A if k not in ('date', 'time', 'time2', 'pcD', 'bonus', 'pc_oct')]
for f in sorted(glob.glob(f'{new}/*.py')):
    s = open(f).read(); o = s
    for a, b in ids: s = s.replace(a, b)
    s = s.replace(f"'{prev}/", f"'{new}/").replace(f"startswith('{prev}')", f"startswith('{new}')")
    if s != o: open(f, 'w').write(s)
DM = lambda d: d.strftime('%d/%m/%Y')
Dm1 = (db - dt.timedelta(1)).isoformat()
edit('ref_exec.py', [(f"X['partial']='{da.isoformat()}'", f"X['partial']='{db.isoformat()}'"),
                     (f"print('Oct NRU',sum(r[E['NRU']] for r in new['{O}']),'FDU',sum(r[E['FDU']] for r in new['{O}']))",
                      f"print('{N} NRU',sum(r[E['NRU']] for r in new['{N}']),'FDU',sum(r[E['FDU']] for r in new['{N}']))")])
open(f'{new}/ref_mkt.py', 'w').write(f'''import json,re,collections,sys
sys.argv=['x']; sys.path.insert(0,'.')
from build_prows import load,build,D,P
TR='raw/'
I={{c:i for i,c in enumerate(P)}}
prev=build(load(TR+'{R['pc_oct']}.txt'),'{O}')     # final {O} (fixed)
cur=build(load(TR+'{B['pc_oct']}.txt'),'{N}')
def rows_for(ym,cur,prevAct,acq):
    keys=set(cur)|{{k for k,o in prevAct.items() if o['Act']>0}}
    out=[]
    for k in sorted(keys):
        a,rg,ci=k; o=cur.get(k,collections.defaultdict(float))
        row=[ym,a,rg,ci]
        for c in P[4:]:
            if c=='UP': row.append(float(o.get('Act',0)))
            elif c=='PA': row.append(float(prevAct.get(k,{{}}).get('Act',0)))
            elif c=='Acq': row.append(acq.get(a,0))
            else:
                v=o.get(c,0); row.append(round(v,2) if isinstance(v,float) else float(v))
        out.append(row)
    return out
acq={{r[1]:r[I['Acq']] for r in D['prows'] if r[0]=='{N}'}}
newN=rows_for('{N}',cur,prev,acq)
old=[r for r in D['prows'] if r[0]=='{N}']
print('{N}','rows',len(old),'->',len(newN))
for c in ['NRU','FDU','Act','Dep','VB','GGR','PA','RT']:
    print('  ',c, round(sum(r[I[c]] for r in old),1), round(sum(r[I[c]] for r in newN),1))
print('{O} rows kept',sum(1 for r in D['prows'] if r[0]=='{O}'))
json.dump({{'cur':newN,'month':'{N}'}},open('{new}/prows_new.json','w'))
''')
_mk = open(f'{new}/mk.py').read()
_ms = "MS=json.load(open('state/config.json'))['month']+'-01'   # current month start (not a literal: newrun would shift it)\n"
if f"r[0]<'{O}-01'" in _mk:   # literal month start -> read it from state/config.json (fix first made in r04m)
    _old = re.search(r"\nold=\{.*?r\[0\]>='" + O + r"-01'\}\n", _mk).group(0)
    edit('mk.py', [(_old, '\n' + _ms + _old[1:].replace(f"r[0]>='{O}-01'", "r[0]>=MS")), (f"r[0]<'{O}-01'", "r[0]<MS")])
edit('mk.py', [
               (f"D['prows']=[r for r in D['prows'] if r[0] not in ('{P}','{O}')]+po['sep']+po['oct']", "D['prows']=[r for r in D['prows'] if r[0]!=po['month']]+po['cur']"),
               (re.search(r"D\['dlast'\]=.*", open(f'{new}/mk.py').read()).group(0), f"D['dlast']='{Dm1}'; D['factmax']='{db.isoformat()}'; D['asof']='{db.isoformat()} {B['time']}:00'")])
edit('ref_prod.py', [(f"mi=PM['m'].index('{O}'); si=PM['m'].index('{P}')", f"mi=PM['m'].index('{N}'); si=PM['m'].index('{O}')"),
                     (re.search(r"DAYS=\[str\(dt\.date\(.*?\)\) for i in range\(\d+\)\]", open(f'{new}/ref_prod.py').read()).group(0), f"DAYS=[str(dt.date({yN},{mN},1)+dt.timedelta(i)) for i in range({db.day})]"),
                     (f"cdOct=PM['cd']['m'].index('{O}')", f"cdOct=PM['cd']['m'].index('{N}')"),
                     (f"ym='{O}'", f"ym='{N}'"), (f"[cdOct,{da.day},c]", f"[cdOct,{db.day},c]"),
                     (f"X['partial']='{da.isoformat()}'; PM['dlast']='{da.isoformat()}'", f"X['partial']='{db.isoformat()}'; PM['dlast']='{db.isoformat()}'")])
rng = lambda f: re.search(r"for i in range\(\d+\)\]", open(f'{new}/{f}').read()).group(0)
for f in ('build_vip2s.py', 'build_vip3s.py'):
    s = open(f'{new}/{f}').read(); loop = re.search(r"months=\[\]; y,m=\d+,\d+\nwhile \(y,m\)<=\(\d+,\d+\)", s).group(0)
    edit(f, [(loop, f"months=[]; y,m={y0},{m0}\nwhile (y,m)<=({yN},{mN})"), (rng(f), f"for i in range({(db - day0).days + 1})]")])
edit('build_vip3s.py', [(f"fx.get('{O}|'+cid,0)", f"fx.get('{N}|'+cid,0)"),
                        (re.search(r"'partial':'[^']*','dpartial':'[^']*','dlast':'[^']*'", open(f'{new}/build_vip3s.py').read()).group(0), f"'partial':'{N}','dpartial':'{db.isoformat()}','dlast':'{db.isoformat()}'"),
                        (re.search(r"'ref':'[^']*'", open(f'{new}/build_vip3s.py').read()).group(0), f"'ref':'{db.isoformat()}'"),
                        (re.search(r"'asof':'[^']*'", open(f'{new}/build_vip3s.py').read()).group(0), f"'asof':'{db.isoformat()} {B['time2']}'")])
edit('build_mg.py', [(re.search(r"'partial':'[^']*','dlast':'[^']*','dpart':'[^']*'", open(f'{new}/build_mg.py').read()).group(0), f"'partial':'{N}','dlast':'{Dm1}','dpart':'{db.isoformat()}'")])
edit('mg_rd.py', [(f"('{new}/RDoct','{O}')", f"('{prev}/RDoct','{O}'),('{new}/RDoct','{N}')"),
                  (f"f.startswith('{new}')", f"f.startswith('r')")])
s = open(f'{new}/final.py').read()
s = re.sub(r"R=\[.*?\]\n", f"R=[('{DM(da)} {A['time']}','{DM(db)} {B['time']}'),('{DM(da)} {A['time2']}','{DM(db)} {B['time2']}')]\n", s); open(f'{new}/final.py', 'w').write(s)
# build_top.py: the old month's bonus pull becomes a fixed part (cut at the new month), then the new pull
s = open('build_top.py').read(); old = f"+load(TR+'{A['bonus']}.txt')"; assert s.count(old) == 1, 'bonus id not found once in build_top.py'
s = s.replace(old, f"+[x for x in load(TR+'{A['bonus']}.txt') if dkey(x[0])<'{N}-01']+load(TR+'{B['bonus']}.txt')"); open('build_top.py', 'w').write(s)
print('build_top.py bonus: fixed', A['bonus'], '<', N, '+ new', B['bonus'])
print('done', new)
