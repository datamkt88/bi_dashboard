"""Month rollover, run ONCE before the first build of a new month (RUNBOOK section 5).

python3 rollover.py <last folder of old month> <new month YYYY-MM>     e.g. python3 rollover.py r31 2026-11

What it does (old month = the month of <last folder>, assumed final):
 1. FX: adds <new month>|<CurrencyId> rates (Fabric exchangerate, RateType 2, rate dated the 1st) to the
    data block. Rates already in the page are never changed.
 2. Data block: cmonths window moves one month (last 12 complete + the new partial month), partial = new
    month, reg list gets the new month, customer month bits shift down by one (bit j = cmonths[j]).
 3. Product block: new month appended to PM['m'] and PM['cd']['m']; PM['partial'] = new month.
 4. state/: config (cut = 1st of new month, month = new month, month_bit = 12), custs_base = last
    folder's custs_in shifted by one bit, per-customer daily chunks of the old month frozen into
    pc_day_hist.json / pc_new_fixed.json, pc_month[old month] = last folder's pcM (final).
 5. state/rollover_<new>.json records the old month's fixed pull ids (bonus, RDoct, pcD, pcM, pc_oct)
    for the new month's run-folder scripts (see mkmonth.py).
"""
import sys, json, re, datetime as dt
sys.path.insert(0, 'cloud')
last, NEW = sys.argv[1], sys.argv[2]
I = json.load(open(f'{last}/ids.json'))
OLD = I['date'][:7]
y, m = map(int, NEW.split('-')); assert (dt.date(y, m, 1) - dt.timedelta(1)).strftime('%Y-%m') == OLD, 'new month must follow the last folder month'
H = open('B2C-Marketing.html', encoding='utf-8').read()
def blk(n): return re.search(r'<script id="%s" type="application/json">(.*?)</script>' % n, H, re.S)
D = json.loads(blk('data').group(1)); PM = json.loads(blk('pmdata').group(1))
# 1 FX
import pbiq
X = "'SiebogMap2 exchangerate'"
out = 'raw/_fx_%s.txt' % NEW
pbiq.run('MK', f'EVALUATE SELECTCOLUMNS(FILTER({X}, {X}[RateType]=2 && {X}[RateDate]=dt"{NEW}-01" && {X}[TargetCurrencyId]=3), "c",{X}[CurrencyId],"r",{X}[Rate])', out)
t = ''.join(x['text'] for x in json.load(open(out))); rows = [r.split(',') for r in t[t.index('] ') + 2:].strip().split('\n')[1:] if r]
rate = {c: float(r) for c, r in rows}
need = sorted({k.split('|')[1] for k in D['fx'] if k.startswith(OLD + '|')})
missing = [c for c in need if c not in rate]
assert not missing, f'no {NEW} rate for currencies {missing}'
for c in need: D['fx'].setdefault(f'{NEW}|{c}', rate[c])
print('fx', NEW, {c: rate[c] for c in need})
# 2 data block
assert D['cmonths'][-1] == OLD, D['cmonths']
D['cmonths'] = D['cmonths'][1:] + [NEW]; D['partial'] = NEW
if NEW not in D['reg']: D['reg'].append(NEW)
D['custs'] = [[a, r, mk >> 1, c] for a, r, mk, c in D['custs'] if mk >> 1]
print('cmonths', D['cmonths'][0], '-', D['cmonths'][-1], 'custs', len(D['custs']))
# 3 product block
for L in (PM['m'], PM['cd']['m']):
    if NEW not in L: L.append(NEW)
PM['partial'] = NEW
H = H[:blk('data').start(1)] + json.dumps(D, separators=(',', ':'), ensure_ascii=False) + H[blk('data').end(1):]
H = H[:blk('pmdata').start(1)] + json.dumps(PM, separators=(',', ':')).replace('</', '<\\/') + H[blk('pmdata').end(1):]
open('B2C-Marketing.html', 'w', encoding='utf-8').write(H)
# 4 state
json.dump({'cut': f'{NEW}-01', 'month': NEW, 'month_bit': 12}, open('state/config.json', 'w'))
ci = json.load(open(f'{last}/custs_in.json'))
json.dump({'act': [[str(int(b) - 1), c] for b, c in ci['act'] if int(b) >= 1], 'cu': ci['cu']}, open('state/custs_base.json', 'w'))
hist = json.load(open('state/pc_day_hist.json'))
json.dump(hist + [x for x in I['pcD'] if x not in hist], open('state/pc_day_hist.json', 'w'))
fixed = json.load(open('state/pc_new_fixed.json')) if __import__('os').path.exists('state/pc_new_fixed.json') else ['1791785152514']
json.dump(fixed + [x for x in I['pcD'] if x not in fixed], open('state/pc_new_fixed.json', 'w'))
pm = json.load(open('pc_month.json')); pm[OLD] = I['pcM']; json.dump(pm, open('pc_month.json', 'w'))
json.dump({'old': OLD, 'new': NEW, 'folder': last, 'bonus': I['bonus'], 'pcD': I['pcD'], 'pcM': I['pcM'], 'pc_oct': I['pc_oct']}, open(f'state/rollover_{NEW}.json', 'w'), indent=1)
print('state updated: config, custs_base (', len(ci['act']), 'act ), pc_day_hist, pc_new_fixed, pc_month[', OLD, ']')
