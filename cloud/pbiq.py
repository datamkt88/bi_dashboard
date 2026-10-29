"""Run a DAX query through the Power BI REST executeQueries API with the app account and
save it in the same raw format the pipeline reads (CSV after '] ', dates as d/m/yyyy h:mm:ss AM)."""
import requests, json, sys, csv, io, datetime, re, os, time
T='84bc7d6a-bd5d-4487-b569-950d8f72b7cd'; A='b5857566-ccdd-4ea9-bd76-84e83d13d979'; S=os.environ.get('PBI_SECRET') or (open(os.path.expanduser('~/.pbi_secret')).read().strip() if os.path.exists(os.path.expanduser('~/.pbi_secret')) else None)
if not S: raise SystemExit('No app secret: put it in ~/.pbi_secret (chmod 600) or env PBI_SECRET')
DS={'MK':('b20227c7-6c43-48f3-ae53-6d24dc06061e','86ac5715-96a2-42b8-ba23-ccf19ff4b87d'),
    'PR':('b20227c7-6c43-48f3-ae53-6d24dc06061e','bb34bb51-411d-405a-aaf3-ad7faa057b10'),
    'PP':('d7df0055-39db-4d9c-8a1b-e6abb5cbf378','c02c66ea-d909-4b6d-a045-e30e750f99a6')}
_tok=None
def token():
    global _tok
    if _tok and _tok[1]>time.time()+120: return _tok[0]
    r=requests.post(f'https://login.microsoftonline.com/{T}/oauth2/v2.0/token',data={'grant_type':'client_credentials','client_id':A,'client_secret':S,'scope':'https://analysis.windows.net/powerbi/api/.default'},timeout=30); r.raise_for_status()
    j=r.json(); _tok=(j['access_token'],time.time()+int(j['expires_in'])); return _tok[0]
ISO=re.compile(r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})')
def fmt(v):
    if v is None: return ''
    if isinstance(v,bool): return 'True' if v else 'False'
    if isinstance(v,str):
        m=ISO.match(v)
        if m:
            y,mo,d,h,mi,s=map(int,m.groups()); ap='AM' if h<12 else 'PM'; h12=h%12 or 12
            return f'{d}/{mo}/{y} {h12}:{mi:02d}:{s:02d} {ap}'
        return v
    if isinstance(v,float) and v.is_integer() and abs(v)<1e15: return str(int(v))
    return str(v)
def run(conn, query, out):
    g,d=DS[conn]
    for attempt in range(3):
        r=requests.post(f'https://api.powerbi.com/v1.0/myorg/groups/{g}/datasets/{d}/executeQueries',headers={'Authorization':'Bearer '+token()},
            json={'queries':[{'query':query}],'serializerSettings':{'includeNulls':True}},timeout=600)
        if r.status_code==429 or r.status_code>=500: time.sleep(20*(attempt+1)); continue
        break
    if not r.ok: raise SystemExit(f'{conn} HTTP {r.status_code}: {r.text[:500]}')
    res=r.json()['results'][0]
    if 'error' in res: raise SystemExit(f"{conn} error: {res['error']}")
    rows=res['tables'][0].get('rows',[])
    cols=list(rows[0].keys()) if rows else []
    buf=io.StringIO(); w=csv.writer(buf,lineterminator='\n'); w.writerow(cols)
    for row in rows: w.writerow([fmt(row.get(c)) for c in cols])
    json.dump([{'type':'text','text':'{"success":true}[Resource from cloud executeQueries] '+buf.getvalue()}],open(out,'w'))
    return len(rows), cols
if __name__=='__main__':
    conn,qf,out=sys.argv[1:4]
    n,c=run(conn,open(qf).read(),out); print(out,n,'rows',c[:6])
