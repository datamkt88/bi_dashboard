"""Append new products/vendors from state/prod_extra.json to the page's pmdata (idempotent).
Products and vendors are stored by index everywhere, so new ones are only ever appended."""
import json, re
F = 'B2C-Marketing.html'
H = open(F, encoding='utf-8').read()
pat = r'(<script id="pmdata" type="application/json">)(.*?)(</script>)'
m = re.search(pat, H, re.S); PM = json.loads(m.group(2))
X = json.load(open('state/prod_extra.json')); add = []
for v in X.get('provs', []):
    if v not in PM['provs']: PM['provs'].append(v); add.append(v)
names = [p[0] for p in PM['prods']]
for n, cat in X.get('prods', []):
    if n not in names:
        PM['prods'].append([n, PM['cats'].index(cat)]); PM.setdefault('prodProv', []).append([]); add.append(n)
if PM.get('prodProv') and len(PM['prodProv']) < len(PM['prods']):
    PM['prodProv'] += [[] for _ in range(len(PM['prods']) - len(PM['prodProv']))]
if add:
    H = H[:m.start(2)] + json.dumps(PM, separators=(',', ':')).replace('</', '<\\/') + H[m.end(2):]
    open(F, 'w', encoding='utf-8').write(H)
print('prodadd', add or 'nothing new', 'prods', len(PM['prods']), 'provs', len(PM['provs']))
