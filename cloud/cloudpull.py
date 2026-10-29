"""Pull every query for date D through the Power BI REST API (app account) into raw/<id>.txt
and write ids_<run>.json. usage: python3 cloudpull.py <pipe dir> <D> <run> [time time2]"""
import sys, os, json, re, subprocess, time, threading, datetime as dt
from concurrent.futures import ThreadPoolExecutor
LOCK=threading.Lock()
W=int(os.environ.get('CLOUD_WORKERS','1'))  # 1 = one query at a time; more can exceed Fabric capacity
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # pbiq.py lives next to this file
import pbiq
P, D, RUN = sys.argv[1:4]
os.chdir(P)
subprocess.run([sys.executable, 'queries.py', D], check=True, stdout=subprocess.DEVNULL)
conn = {}
for l in open('queries/INDEX.txt'):
    m = re.match(r'^(\S+)\s+(MK|PR|PP)\s', l)
    if m: conn[m.group(1)] = m.group(2)
names = [n for n in conn if not n.startswith('_')]
ids = {'date': D, 'time': sys.argv[4] if len(sys.argv) > 4 else time.strftime('%H:%M'), 'time2': sys.argv[5] if len(sys.argv) > 5 else time.strftime('%H:%M')}
base = int(time.time() * 1000)
def save(name, q):
    global base
    cn=conn[name.split('.')[0]]
    with LOCK:
        base += 1; rid = f'9{base}'
    for k in range(4):
        try:
            n, c = pbiq.run(cn, q, f'raw/{rid}.txt'); break
        except Exception as e:
            if k == 3: raise
            print('  retry', name, str(e)[:120]); time.sleep(10)
    print(f'{name:10s} {cn} {n:7d} rows -> {rid}', flush=True); return rid
pcD = []
TB="'WS_BIReport TpBetRecordSummaryDailyMonthly_Output'"
def merge(parts):
    global base
    rows=[]; hdr=None
    LOCK.acquire()
    for rid in parts:
        t=''.join(x['text'] for x in json.load(open(f'raw/{rid}.txt'))); body=t[t.index('] ')+2:]
        lines=body.split('\n'); hdr=lines[0]; rows+=[l for l in lines[1:] if l]
        os.remove(f'raw/{rid}.txt')
    base+=1; rid=f'9{base}'
    LOCK.release()
    json.dump([{'type':'text','text':'{"success":true}[Resource from cloud executeQueries] '+hdr+'\n'+'\n'.join(rows)+'\n'}],open(f'raw/{rid}.txt','w'))
    return rid, len(rows)
def split_save(name, q, N=4):
    # per-customer TpBet pulls are > 15 MB as JSON: split by CustId modulo N and merge
    assert q.rstrip().endswith(')')
    parts=[]
    qs=[(name+f'.{i}', q.rstrip()[:-1]+f", FILTER(VALUES({TB}[CustId]), MOD({TB}[CustId],{N})={i}))") for i in range(N)]
    with ThreadPoolExecutor(W) as ex: parts=list(ex.map(lambda a: save(*a), qs))
    rid,n=merge(parts); print(f'{name} merged {n} rows -> {rid}', flush=True); return rid
simple=[n for n in names if n!='list2' and n!='pcM' and not n.startswith('pcD')]
with ThreadPoolExecutor(W) as ex:
    for n,rid in zip(simple, ex.map(lambda n: save(n, open(f'queries/{n}.dax').read()), simple)): ids[n]=rid
for name in [n for n in names if n not in simple]:
    q = open(f'queries/{name}.dax').read()
    if name == 'list2':   # > 1M values: split by customer id range
        parts = []
        for lo, hi in ((1750000, 1900000), (1900000, 9999999999)):
            qq = q.replace('view_CustomerProfile[CustId]>1750000', f'view_CustomerProfile[CustId]>{lo} && view_CustomerProfile[CustId]<={hi}')
            assert qq != q
            parts.append(save(name, qq))
        # merge the two parts into one raw file
        import csv, io
        rows = []; hdr = None
        for rid in parts:
            t = ''.join(x['text'] for x in json.load(open(f'raw/{rid}.txt'))); body = t[t.index('] ') + 2:]
            lines = body.split('\n'); hdr = lines[0]; rows += [l for l in lines[1:] if l]
        base += 1; rid = f'9{base}'
        json.dump([{'type': 'text', 'text': '{"success":true}[Resource from cloud executeQueries] ' + hdr + '\n' + '\n'.join(rows) + '\n'}], open(f'raw/{rid}.txt', 'w'))
        print(f'list2 merged {len(rows)} rows -> {rid}'); ids['list2'] = rid
    elif name.startswith('pcD') or name=='pcM':
        rid = split_save(name, q)
        if name=='pcM': ids[name]=rid
        else: pcD.append(rid)
    else: ids[name] = save(name, q)
ids['pcD'] = pcD
json.dump(ids, open(f'ids_{RUN}.json', 'w'), indent=1)
print('wrote', f'ids_{RUN}.json')
