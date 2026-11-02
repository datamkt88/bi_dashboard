"""Keep marketing-overview history the source model no longer returns.

The Marketing model's FullSummary table keeps a rolling window (on 1 Nov 2026 it dropped Sep 2025
monthly and Jul 2026 daily rows), so a fresh mg_m / mg_d pull can start later than the previous build.
Those older periods are final, so carry them over from the previous run's mgdata.json.

python3 mg_keep.py rPREV/mgdata.json rNEW/mgdata.json      (rewrites rNEW/mgdata.json in place)
"""
import json, sys
prev, new = sys.argv[1], sys.argv[2]
A = json.load(open(prev)); B = json.load(open(new))
assert A['cols'] == B['cols'], 'column layout changed'
cells = [list(c) for c in B['cells']]; segs = [list(s) for s in B['segs']]
def ix(lst, v):
    v = list(v)
    if v not in lst: lst.append(v)
    return lst.index(v)
def carry(per_a, per_b, rows_a, rows_b):
    old = [p for p in per_a if p < per_b[0]]          # periods before the new pull's first one
    if not old: return per_b, rows_b, 0
    per = old + per_b; pi = {p: i for i, p in enumerate(per)}
    out = []
    for r in rows_a:
        p = per_a[r[0]]
        if p in old: out.append([pi[p], ix(cells, A['cells'][r[1]]), ix(segs, A['segs'][r[2]])] + r[3:])
    for r in rows_b:
        out.append([pi[per_b[r[0]]], ix(cells, B['cells'][r[1]]), ix(segs, B['segs'][r[2]])] + r[3:])
    return per, out, len(old)
B['m'], B['M'], nm = carry(A['m'], B['m'], A['M'], B['M'])
B['days'], B['D'], nd = carry(A['days'], B['days'], A['D'], B['D'])
B['cells'] = cells; B['segs'] = segs
json.dump(B, open(new, 'w'), separators=(',', ':'), ensure_ascii=False)
print('mg_keep: carried', nm, 'months and', nd, 'days from', prev, '| months', B['m'][0], '-', B['m'][-1], '| days', B['days'][0], '-', B['days'][-1])
