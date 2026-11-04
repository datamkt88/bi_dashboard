"""Set the page's FX rates for one month to Power BI's current rates (Fabric exchangerate, RateType 2,
rate dated the 1st, to USD). Power BI revises a month's rate after the month starts, so run.sh calls this
before every build for the month being built (state/config.json 'month'); every block of that month is then
rebuilt with the same rates. Older months are never touched.

python3 fxsync.py [YYYY-MM]        (default: state/config.json month)
"""
import sys, json, re
sys.path.insert(0, 'cloud'); import pbiq
M = sys.argv[1] if len(sys.argv) > 1 else json.load(open('state/config.json'))['month']
H = open('B2C-Marketing.html', encoding='utf-8').read()
b = re.search(r'<script id="data" type="application/json">(.*?)</script>', H, re.S)
D = json.loads(b.group(1))
X = "'SiebogMap2 exchangerate'"
out = f'raw/_fx_{M}.txt'
pbiq.run('MK', f'EVALUATE SELECTCOLUMNS(FILTER({X}, {X}[RateType]=2 && {X}[RateDate]=dt"{M}-01" && {X}[TargetCurrencyId]=3), "c",{X}[CurrencyId],"r",{X}[Rate],"pad",REPT("x",400))', out)
t = ''.join(x['text'] for x in json.load(open(out)))
rate = {r.split(',')[0]: float(r.split(',')[1]) for r in t[t.index('] ') + 2:].strip().split('\n')[1:] if r}
need = sorted({k.split('|')[1] for k in D['fx'] if k.startswith(M + '|')})
missing = [c for c in need if c not in rate]
assert not missing, f'Power BI has no {M} rate for currencies {missing}'
ch = {c: (D['fx'][f'{M}|{c}'], rate[c]) for c in need if D['fx'][f'{M}|{c}'] != rate[c]}
for c in need: D['fx'][f'{M}|{c}'] = rate[c]
H = H[:b.start(1)] + json.dumps(D, separators=(',', ':'), ensure_ascii=False) + H[b.end(1):]
open('B2C-Marketing.html', 'w', encoding='utf-8').write(H)
print('fxsync', M, len(need), 'currencies,', len(ch), 'changed', ch)
