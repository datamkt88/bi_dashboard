import json,re,csv,io,sys,collections
H=open('B2C-Marketing.html',encoding='utf-8').read()
D=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',H,re.S).group(1))
fx=D['fx']; P=D['pcols']
def load(fn):
    j=json.load(open(fn)); t=''.join(x.get('text','') for x in j); t=t[t.index('] ')+2:]
    return [r for r in list(csv.reader(io.StringIO(t)))[1:] if r]
def regb(s):
    d,m,y=s.split(' ')[0].split('/'); y=int(y); m=int(m)
    return '<2025' if y<2025 else f'{y}-{m:02d}'
def build(rows, ym):
    num=lambda x: float(x) if x else 0.0
    agg=collections.defaultdict(lambda: collections.defaultdict(float))
    # header: CustId,Aff,CurId,RegTime,NRU,FDU,Act,Tx,RD,Dep,FD,W,DF,WF,CM,VB,SB,CB,LB,WL,BO,RB,RT,PRO,ADJ
    for r in rows:
        a,ci,rg=r[1],r[2],regb(r[3])
        NRU,FDU,Act,Tx,RD,Dep,FD,W,DF,WF,CM,VB,SB,CB,LB,WL,BO,RB,RT,PRO,ADJ=[num(x) for x in r[4:]]
        f=fx[ym+'|'+ci]; o=agg[(a,rg,ci)]
        o['NRU']+=NRU; o['FDU']+=FDU; o['Act']+=1 if Act>0 else 0; o['Tx']+=Tx; o['RD']+=1 if RD>0 else 0
        for k,v in (('Dep',Dep),('FD',FD),('W',W),('DF',DF),('WF',WF),('CM',CM),('VB',VB),('SB',SB),('CB',CB),('LB',LB),('BO',BO),('RB',RB),('PRO',PRO),('ADJ',ADJ)): o[k]+=v*f
        o['GGR']+=-WL*f; o['RT']+=1 if RT>0 else 0
    return agg
if __name__=='__main__':
    rows=load(sys.argv[1]); ym=sys.argv[2]
    agg=build(rows,ym)
    old={(r[1],r[2],r[3]):r for r in D['prows'] if r[0]==ym}
    I={c:i for i,c in enumerate(P)}
    for c in ['NRU','FDU','Act','UP','Tx','RD','Dep','FD','W','DF','WF','CM','VB','SB','CB','LB','GGR','BO','RB','PA','RT','PRO','ADJ']:
        a=sum(r[I[c]] for r in old.values()); b=sum(o.get(c if c!='UP' else 'Act',0) for o in agg.values())
        print(c, round(a,2), round(b,2))
    ko=set(old); kn=set(k for k,o in agg.items())
    print('old keys',len(ko),'new',len(kn),'old-only',len(ko-kn), list(ko-kn)[:5],'new-only',len(kn-ko),list(kn-ko)[:5])
    bad=[k for k in ko&kn if any(abs(old[k][I[c]]-agg[k][c])>0.05 for c in ['NRU','FDU','Act','Tx','RD','Dep','VB','GGR','RT'])]
    print('row diffs',len(bad)); [print(k,[ (c,old[k][I[c]],round(agg[k][c],2)) for c in ['NRU','FDU','Act','Tx','RD','Dep','VB','GGR','RT'] if abs(old[k][I[c]]-agg[k][c])>0.05]) for k in bad[:5]]
