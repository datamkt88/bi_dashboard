"""Create the next run folder from the previous one (same month only).

python3 newrun.py r27b r28 ids_r28.json
   ids_r28.json = {"date":"2026-10-28","time":"09:05","time2":"09:09", "exec":"<id>", ... "pcD":["<id>","<id>"], ...}
   (same keys as r27b/ids.json; time = marketing/product pull time, time2 = player-profile pull time)

Copies rPREV -> rNEW, swaps every old pull id for the new one, renames folder references,
moves the dates/times forward, and patches the root scripts that also carry ids (build_top.py bonus).
Prints every replacement so you can eyeball it. For a month rollover, do NOT use this blindly -
see RUNBOOK 'Month rollover'.
"""
import sys, json, shutil, os, glob, re, datetime as dt
prev, new, idsf = sys.argv[1], sys.argv[2], sys.argv[3]
A=json.load(open(f'{prev}/ids.json')); B=json.load(open(idsf))
da,db=dt.date.fromisoformat(A['date']),dt.date.fromisoformat(B['date'])
assert da.strftime('%Y-%m')==db.strftime('%Y-%m'), 'month changed - follow RUNBOOK Month rollover'
if os.path.exists(new): shutil.rmtree(new)
os.makedirs(new)
for f in glob.glob(f'{prev}/*.py'): shutil.copy(f,new)
json.dump(B,open(f'{new}/ids.json','w'),indent=1)
rep=[]
for k,v in A.items():
    if k in('date','time','time2'): continue
    if isinstance(v,list):
        rep+=list(zip(v,B[k])) if len(v)==len(B[k]) else []
    else: rep.append((v,B[k]))
DM=lambda d: d.strftime('%d/%m/%Y')
day0=dt.date(2026,7,1)
pairs=rep+[(f"'{prev}/",f"'{new}/"),(f"('{prev}/",f"('{new}/"),(f"startswith('{prev}')",f"startswith('{new}')"),
 (f"'{(da-dt.timedelta(1)).isoformat()}'","'@@DM1@@'"),(f"'{da.isoformat()}'","'@@D@@'"),(f"'{da.isoformat()} {A['time']}:00'","'@@D@@ @@T@@:00'"),
 (f"'{da.isoformat()} {A['time2']}'","'@@D@@ @@T2@@'"),
 (f"range({da.day})]",f"range({db.day})]"),(f"[cdOct,{da.day},c]",f"[cdOct,{db.day},c]"),
 (f"range({(da-day0).days+1})]",f"range({(db-day0).days+1})]"),
 ("'@@DM1@@'",f"'{(db-dt.timedelta(1)).isoformat()}'"),("'@@D@@'",f"'{db.isoformat()}'"),("'@@D@@ @@T@@:00'",f"'{db.isoformat()} {B['time']}:00'"),("'@@D@@ @@T2@@'",f"'{db.isoformat()} {B['time2']}'")]
for f in sorted(glob.glob(f'{new}/*.py')):
    s=open(f).read(); o=s
    for a,b in pairs:
        n=s.count(a)
        if n and a!=b: s=s.replace(a,b); print(f'{os.path.basename(f):16s} {n}x  {a} -> {b}')
    # display stamps in final.py: previous run's stamps -> this run's
    s=re.sub(r"R=\[.*?\]\n",f"R=[('{DM(da)} {A['time']}','{DM(db)} {B['time']}'),('{DM(da)} {A['time2']}','{DM(db)} {B['time2']}')]\n",s) if f.endswith('final.py') else s
    if s!=o: open(f,'w').write(s)
# root scripts that carry ids
for f in ('build_top.py',):
    s=open(f).read(); o=s
    s=s.replace(A['bonus'],B['bonus'])
    if s!=o: open(f,'w').write(s); print(f,'bonus',A['bonus'],'->',B['bonus'])
print('final.py R ->', re.search(r"R=\[.*?\]",open(f'{new}/final.py').read()).group(0))
