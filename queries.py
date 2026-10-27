"""Generate every DAX query used by the B2C Marketing & OP refresh.

usage:  python3 queries.py 2026-10-28            -> writes queries/<name>.dax for report date D
        python3 queries.py 2026-10-28 --cut 2026-10-06

D      = report date (data through D; D itself is the partial day)
--cut  = first day that is re-pulled for per-customer daily data (pc day, bonus, vipm).
         Everything before CUT lives in state/ (pc_day.json + raw/). Keep 2026-10-06 until
         you deliberately roll the state forward (see RUNBOOK 'Month rollover').

Each query lists: connection (MK / PR / PP), expected header, and a reference result in ref/
(pulled 27 Oct 2026) so a new session can calibrate: run with D=2026-10-27 and compare.
Queries marked VERIFY contain column names that were reconstructed, not copied from a
saved query - if one errors, run queries/_schema_*.dax to see the real column names.
"""
import sys, os, datetime as dt
D = dt.date.fromisoformat(sys.argv[1])
CUT = dt.date.fromisoformat(sys.argv[sys.argv.index('--cut')+1]) if '--cut' in sys.argv else dt.date(2026,10,6)
D1 = D + dt.timedelta(1)
MS = D.replace(day=1)                                   # current month start
PMS = (MS - dt.timedelta(1)).replace(day=1)             # previous month start
NMS = (MS + dt.timedelta(32)).replace(day=1)            # next month start
REF90 = D - dt.timedelta(90)
d = lambda x: 'dt"%s"' % x.isoformat()
def months(n_back):                                     # list of (key,start,end) ending at current month
    out=[]; y,m=MS.year,MS.month
    for _ in range(n_back): out.append((y,m)); y,m=(y-1,12) if m==1 else (y,m-1)
    out=out[::-1]; rows=[]
    for y,m in out:
        s=dt.date(y,m,1); e=(s+dt.timedelta(32)).replace(day=1); rows.append((f'{y}-{m:02d}',s,e))
    return rows
def dtab(rows,k='k'):
    return 'DATATABLE("%s",STRING,"s",DATETIME,"e",DATETIME,{%s})'%(k,','.join('{"%s",%s,%s}'%(a,d(b),d(c)) for a,b,c in rows))
PAD = '"pad",REPT("x",150)'
F="'WS_BIReport FullSummaryDailyMonthly_Output'"; C="'WS_Customer customer'"; T="'WS_BIReport TpBetRecordSummaryDailyMonthly_Output'"; V="view_CustomerProfile"
SITES='TREATAS({"Nova88","Goal123","Bwing"}, %s[SiteName])'%C
MASTER="TREATAS(VALUES('Acquisition Master Channel List'[AffiliateName]), %s[AffiliateName])"%C
Q={}
# ---------------------------------------------------------------- MK = AI Report_Marketing
grid=f'UNION({dtab([(PMS.strftime("%Y-%m"),PMS,MS),(MS.strftime("%Y-%m"),MS,NMS)],"ym")}, SELECTCOLUMNS(CALENDAR({d(MS)},{d(D)}),"ym",FORMAT([Date],"yyyy-mm-dd"),"s",[Date],"e",[Date]+1))'
def S(c): return f"CALCULATE(SUM({F}[{c}]))"
def DC(flag): return f"CALCULATE(DISTINCTCOUNT({F}[CustId]), {F}[{flag}]=1)"
PRO=f"CALCULATE(SUM({F}[PrizeAmount])+SUM({F}[OthRewardAmount])+SUM({F}[ReferralAmount]))"
main_meas=[("NRU",S("NRU_Flag")),("FDU",S("FDU_Flag")),("Act",DC("ActiveUser_Flag")),("Ret",DC("IsMonthlyReturningActiveUser_Flag")),("Depr",DC("Depositor_Flag")),("RD",DC("FDUMonthly_Multi_Redeposit_Flag")),("Tx",S("TpTrnsCnt")),("D",S("DepositAmount")),("FD",S("FirstDepositAmt")),("W",S("WithdrawalAmount")),("DF",S("DepositFee")),("WF",S("WithdrawalChargeFee")),("CM",S("CommissionAmt")),("VB",S("ValidBet")),("SB",S("SportsValidBet")),("CB",S("CasinoValidBet")),("LB",S("LiveCasinoValidBet")),("WL",S("WinLostAmount")),("BO",S("BonusAmount")),("RB",S("RebateAmount")),("PRO",PRO),("ADJ",S("AdjustmentAmount"))]
def gridq(meas,extra=''):
    a=', '.join(f'"{n}", {e}' for n,e in meas); b=', '.join(f'"{n}", [{n}]' for n,_ in meas)
    return (f"DEFINE VAR M = {grid}\nEVALUATE SELECTCOLUMNS(GENERATE(M, VAR s=[s] VAR e=[e] RETURN CALCULATETABLE(ADDCOLUMNS(SUMMARIZE({F},{C}[SiteName],{C}[Currency],{C}[CurrencyId]), {a}), "
            f"{F}[ReportDate]>=s, {F}[ReportDate]<e, {SITES}{extra})), \"m\",[ym],\"Si\",{C}[SiteName],\"Cu\",{C}[Currency],\"Ci\",{C}[CurrencyId], {b}, {PAD})")
Q['exec']=('MK','[m],[Si],[Cu],[Ci],[NRU],[FDU],[Act],[Ret],[Depr],[RD],[Tx],[D],[FD],[W],[DF],[WF],[CM],[VB],[SB],[CB],[LB],[WL],[BO],[RB],[PRO],[ADJ],[pad]',gridq(main_meas))
Q['mkt']=('MK','[m],[Si],[Cu],[Ci],[MktNRU],[MktFDU],[MktDep],[MktGGR],[pad]',gridq([("MktNRU",S("NRU_Flag")),("MktFDU",S("FDU_Flag")),("MktDep",S("DepositAmount")),("MktGGR",f"CALCULATE(-SUM({F}[WinLostAmount]))")],', '+MASTER))
pc_meas=[("NRU",f"SUM({F}[NRU_Flag])"),("FDU",f"SUM({F}[FDU_Flag])"),("Act",f"CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[ActiveUser_Flag]=1)"),("Tx",f"SUM({F}[TpTrnsCnt])"),("RD",f"CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[FDUMonthly_Multi_Redeposit_Flag]=1)"),("Dep",f"SUM({F}[DepositAmount])"),("FD",f"SUM({F}[FirstDepositAmt])"),("W",f"SUM({F}[WithdrawalAmount])"),("DF",f"SUM({F}[DepositFee])"),("WF",f"SUM({F}[WithdrawalChargeFee])"),("CM",f"SUM({F}[CommissionAmt])"),("VB",f"SUM({F}[ValidBet])"),("SB",f"SUM({F}[SportsValidBet])"),("CB",f"SUM({F}[CasinoValidBet])"),("LB",f"SUM({F}[LiveCasinoValidBet])"),("WL",f"SUM({F}[WinLostAmount])"),("BO",f"SUM({F}[BonusAmount])"),("RB",f"SUM({F}[RebateAmount])"),("RT",f"CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[IsMonthlyReturningActiveUser_Flag]=1)"),("PRO",f"SUM({F}[PrizeAmount])+SUM({F}[OthRewardAmount])+SUM({F}[ReferralAmount])"),("ADJ",f"SUM({F}[AdjustmentAmount])")]
Q['pc_oct']=('MK','WS_Customer customer[CustId],[AffiliateName],[CurrencyId],[RegTime_utc8],[NRU],[FDU],[Act],[Tx],[RD],[Dep],[FD],[W],[DF],[WF],[CM],[VB],[SB],[CB],[LB],[WL],[BO],[RB],[RT],[PRO],[ADJ]',
  f"EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({C}[CustId],{C}[AffiliateName],{C}[CurrencyId],{C}[RegTime_utc8], "+', '.join(f'"{n}", {e}' for n,e in pc_meas)+f"), {F}[ReportDate]>={d(MS)}, {F}[ReportDate]<{d(NMS)}, {SITES}, {MASTER})")
dr_meas=[("NRU",f"SUM({F}[NRU_Flag])"),("FDU",f"SUM({F}[FDU_Flag])"),("Act",f"CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[ActiveUser_Flag]=1)"),("Tx",f"SUM({F}[TpTrnsCnt])"),("Dep",f"SUM({F}[DepositAmount])"),("FD",f"SUM({F}[FirstDepositAmt])"),("W",f"SUM({F}[WithdrawalAmount])"),("VB",f"SUM({F}[ValidBet])"),("G1",f"-SUM({F}[WinLostAmount])"),("BO",f"SUM({F}[BonusAmount])"),("RB",f"SUM({F}[RebateAmount])"),("PRO",f"SUM({F}[PrizeAmount])+SUM({F}[OthRewardAmount])+SUM({F}[ReferralAmount])"),("ADJ",f"SUM({F}[AdjustmentAmount])")]
Q['drows']=('MK','FullSummary[ReportDate],customer[AffiliateName],customer[CurrencyId],[NRU],[FDU],[Act],[Tx],[Dep],[FD],[W],[VB],[G1],[BO],[RB],[PRO],[ADJ]',
  f"EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({F}[ReportDate],{C}[AffiliateName],{C}[CurrencyId], "+', '.join(f'"{n}", {e}' for n,e in dr_meas)+f"), {F}[ReportDate]>={d(MS)}, {F}[ReportDate]<{d(D1)}, {C}[RegTime_utc8]>=dt\"2025-01-01\", {SITES}, {MASTER})")
A="'Acquisition Report Consolidate New'"
Q['srows']=('MK','Acq[ReportDate],Acq[Affiliate User],[Sp],[Im],[Cl],[n]   VERIFY Impression/Click column names',
  f'EVALUATE SUMMARIZECOLUMNS({A}[ReportDate],{A}[Affiliate User], "Sp", SUM({A}[Spend]), "Im", SUM({A}[Impression]), "Cl", SUM({A}[Click]), "n", COUNTROWS({A}))')
L="'Acquisition Master Channel List'"
Q['aff']=('MK','[a],[code],[ch],[src],[mkt],[site],[pic],[pf],[own],[pad]   VERIFY column names except AffiliateName/Channel/Market',
  f'EVALUATE SELECTCOLUMNS({L}, "a",{L}[AffiliateName], "code",{L}[AffiliateCode], "ch",{L}[Channel], "src",{L}[Source], "mkt",{L}[Market], "site",{L}[Site], "pic",{L}[PIC], "pf",{L}[Platform], "own",{L}[Owner], {PAD})')
Q['bonus']=('MK','FullSummary[ReportDate],FullSummary[CustId],[b]',
  f'EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({F}[ReportDate],{F}[CustId], "b", SUM({F}[BonusAmount])), {F}[TableType]="Daily", {F}[BonusAmount]<>0, {F}[ReportDate]>={d(CUT)}, {F}[ReportDate]<{d(D1)})')
Q['vipm_fd']=('MK','FullSummary[CustId],FullSummary[ReportDate],customer[SiteName],customer[CurrencyId],[f]',
  f'EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({F}[CustId],{F}[ReportDate],{C}[SiteName],{C}[CurrencyId], "f", SUM({F}[FDU_Flag])), {F}[FDU_Flag]=1, {F}[ReportDate]>={d(CUT)}, {F}[ReportDate]<{d(D1)}, {SITES})')
Q['vipm_nr']=('MK','FullSummary[CustId],FullSummary[ReportDate],[n]',
  f'EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({F}[CustId],{F}[ReportDate], "n", SUM({F}[NRU_Flag])), {F}[NRU_Flag]=1, {F}[ReportDate]>={d(CUT)}, {F}[ReportDate]<{d(D1)}, {SITES})')
# marketing overview (mg) - segments = MarketingGroup x MarketingChannel x MarketingType
SEG=f"{C}[SiteName],{C}[CurrencyId],{C}[MarketingGroup],{C}[MarketingChannel],{C}[MarketingType]"
mg_meas=[("NRU",f"SUM({F}[NRU_Flag])"),("FDU",f"SUM({F}[FDU_Flag])"),("Act",f"CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[ActiveUser_Flag]=1)"),("Depr",f"CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[Depositor_Flag]=1)"),("RD",f"CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[FDUMonthly_Multi_Redeposit_Flag]=1)"),("Dep",f"SUM({F}[DepositAmount])"),("FD",f"SUM({F}[FirstDepositAmt])"),("W",f"SUM({F}[WithdrawalAmount])"),("VB",f"SUM({F}[ValidBet])"),("WL",f"SUM({F}[WinLostAmount])"),("BO",f"SUM({F}[BonusAmount])"),("RB",f"SUM({F}[RebateAmount])"),("PRO",f"SUM({F}[PrizeAmount])+SUM({F}[OthRewardAmount])+SUM({F}[ReferralAmount])"),("ADJ",f"SUM({F}[AdjustmentAmount])")]
am=', '.join(f'"{n}", CALCULATE({e})' for n,e in mg_meas); bm=', '.join(f'"{n}", [{n}]' for n,_ in mg_meas)
Q['mg_m']=('MK','[k],[d0],[d1],[d2],[d3],[d4],[NRU],[FDU],[Act],[Depr],[RD],[Dep],[FD],[W],[VB],[WL],[BO],[RB],[PRO],[ADJ]',
  f"DEFINE VAR M = {dtab(months(14))}\nEVALUATE SELECTCOLUMNS(GENERATE(M, VAR s=[s] VAR e=[e] RETURN CALCULATETABLE(ADDCOLUMNS(SUMMARIZE({F},{SEG}), {am}), {F}[ReportDate]>=s, {F}[ReportDate]<e, {SITES})), \"k\",[k], \"d0\",{C}[SiteName], \"d1\",{C}[CurrencyId], \"d2\",{C}[MarketingGroup], \"d3\",{C}[MarketingChannel], \"d4\",{C}[MarketingType], {bm})")
Q['mg_d']=('MK','FullSummary[ReportDate],customer[SiteName],[CurrencyId],[MarketingGroup],[MarketingChannel],[MarketingType],[NRU],[FDU],[Act],[Depr],[RD],[Dep],[FD],[W],[VB],[WL],[BO],[RB],[PRO],[ADJ]',
  f"EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({F}[ReportDate],{SEG}, "+', '.join(f'"{n}", {e}' for n,e in mg_meas)+f"), {F}[TableType]=\"Daily\", {F}[ReportDate]>=dt\"2026-07-01\", {F}[ReportDate]<{d(D1)}, {SITES})")
RDX=f"COUNTROWS(FILTER(VALUES({F}[CustId]), CALCULATE(SUM({F}[Depositor_Flag]))>0 && (CALCULATE(SUM({F}[FDU_Flag]))=0 || CALCULATE(SUM({F}[DepositTrnsCnt]))>1)))"
Q['RDoct']=('MK','customer[SiteName],[CurrencyId],[MarketingGroup],[MarketingChannel],[MarketingType],[Depr],[RD],[pad]   (drop rows where Depr blank)',
  f"EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({SEG}, \"Depr\", CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[Depositor_Flag]=1), \"RD\", {RDX}, {PAD}), {F}[ReportDate]>={d(MS)}, {F}[ReportDate]<{d(NMS)}, {SITES})")
Q['RD_daily']=('MK','FullSummary[ReportDate],customer[SiteName],[CurrencyId],[MarketingGroup],[MarketingChannel],[MarketingType],[Depr],[RD]',
  f"EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({F}[ReportDate],{SEG}, \"Depr\", CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[Depositor_Flag]=1), \"RD\", CALCULATE(DISTINCTCOUNT({F}[CustId]),{F}[Depositor_Flag]=1, KEEPFILTERS(FILTER(ALL({F}[FDU_Flag],{F}[DepositTrnsCnt]), {F}[FDU_Flag]=0 || {F}[DepositTrnsCnt]>1)))), {F}[TableType]=\"Daily\", {F}[ReportDate]>=dt\"2026-07-01\", {F}[ReportDate]<{d(D1)}, {SITES})")
# ---------------------------------------------------------------- PR = AI Report_Product
G=(f'UNION(ROW("g","m","s",{d(MS)},"e",{d(NMS)}), SELECTCOLUMNS(CALENDAR({d(MS)},{d(D)}),"g",FORMAT([Date],"yyyy-mm-dd"),"s",[Date],"e",[Date]+1)'
   + (f', SELECTCOLUMNS(CALENDAR({d(MS+dt.timedelta(1))},{d(D)}),"g","c"&FORMAT(DAY([Date])-1,"0"),"s",{d(MS)},"e",[Date])' if D>MS else '') + ')')
def prod(keys,pad):
    s=','.join(f"{T}[{k}]" for k in ['SiteId','CurrencyId']+keys)
    sel=', '.join(f'"k{i}",{T}[{k}]' for i,k in enumerate(['SiteId','CurrencyId']+keys))
    return (f"DEFINE VAR G = {G}\nEVALUATE SELECTCOLUMNS(GENERATE(G, VAR s=[s] VAR e=[e] RETURN CALCULATETABLE(ADDCOLUMNS(SUMMARIZE({T},{s}), \"wl\", CALCULATE(SUM({T}[WinLossSummary])), \"vb\", CALCULATE(SUM({T}[ValidBetSummary])), \"p\", CALCULATE(DISTINCTCOUNT({T}[CustId]))), {T}[TableType]=\"Daily\", {T}[ReportDate]>=s, {T}[ReportDate]<e)), \"g\",[g], {sel}, \"wl\",[wl],\"vb\",[vb],\"p\",[p]"+(', '+PAD if pad else '')+")")
for n,k,p in (('T',[],1),('C',['Category'],0),('P',['Product'],0),('V',['Provider'],0),('VC',['Provider','Category'],0),('VP',['Provider','Product'],0)):
    Q[n]=('PR','[g],[k0],[k1]'+''.join(f',[k{i+2}]' for i in range(len(k)))+',[wl],[vb],[p]'+(',[pad]' if p else ''),prod(k,p))
PCC=','.join(f"{T}[{k}]" for k in ['CustId','SiteId','CurrencyId','Provider','Product'])
PCM=f'"wl", SUM({T}[WinLossSummary]), "vb", SUM({T}[ValidBetSummary])'
Q['pcM']=('PR','TpBet[CustId],[SiteId],[CurrencyId],[Provider],[Product],[wl],[vb]',f'EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({PCC}, {PCM}), {T}[TableType]="Daily", {T}[ReportDate]>={d(MS)}, {T}[ReportDate]<{d(NMS)})')
mid=CUT+dt.timedelta(10)
Q['pcD1']=('PR','TpBet[ReportDate],[CustId],[SiteId],[CurrencyId],[Provider],[Product],[wl],[vb]',f'EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({T}[ReportDate],{PCC}, {PCM}), {T}[TableType]="Daily", {T}[ReportDate]>={d(CUT)}, {T}[ReportDate]<{d(min(mid,D1))})')
if mid<D1:
    m2=mid+dt.timedelta(11)
    Q['pcD2']=('PR','same as pcD1',f'EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({T}[ReportDate],{PCC}, {PCM}), {T}[TableType]="Daily", {T}[ReportDate]>={d(mid)}, {T}[ReportDate]<{d(min(m2,D1))})')
    if m2<D1: Q['pcD3']=('PR','same as pcD1',f'EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS({T}[ReportDate],{PCC}, {PCM}), {T}[TableType]="Daily", {T}[ReportDate]>={d(m2)}, {T}[ReportDate]<{d(D1)})')
# ---------------------------------------------------------------- PP = Player Profile 360
LST=(f'"c",{V}[CustId], "sb",{V}[Saba_Id], "si",{V}[SiteName], "cu",{V}[CurrencyId], "rg",{V}[RegTime_utc8], "fd",{V}[FirstDepositDate_utc8], "lb",{V}[LastBettingDate_utc8], "ld",{V}[LastDepositDate_utc8], '
     f'"v",{V}[VipLevel], "st",{V}[StatusName], "dc",{V}[LT_DepositCnt], "t",{V}[IsTest], "vb",{V}[LT_EffectiveBet], "wl",{V}[LT_WinLoss], "dp",{V}[LT_Deposit], "nd",{V}[LT_NetDeposit]')
COND=f'{V}[RegTime_utc8]>=dt"2026-07-01" || {V}[LastBettingDate_utc8]>={d(REF90)} || {V}[LastDepositDate_utc8]>={d(REF90)}'
for n,c in (('list1',f'{V}[CustId]<=1750000'),('list2',f'{V}[CustId]>1750000')):
    Q[n]=('PP','[c],[sb],[si],[cu],[rg],[fd],[lb],[ld],[v],[st],[dc],[t],[vb],[wl],[dp],[nd]   VERIFY Saba_Id/StatusName/LastDepositDate_utc8',
          f'EVALUATE SELECTCOLUMNS(FILTER({V}, {c} && {V}[SiteName] IN {{"Nova88","Goal123","Bwing"}} && ({COND})), {LST})')
Q['tags']=('PP','[c],[t]   VERIFY CustTagSummary[CustId]',
  f"EVALUATE CALCULATETABLE(SELECTCOLUMNS(CustTagSummary, \"c\", CustTagSummary[CustId], \"t\", CustTagSummary[TagName]), TREATAS(SELECTCOLUMNS(FILTER({V}, {V}[SiteName] IN {{\"Nova88\",\"Goal123\",\"Bwing\"}} && ({COND})), \"c\", {V}[CustId]), CustTagSummary[CustId]))")
Q['l2']=('PP','[c],[v],[s],[rg]',f'EVALUATE SELECTCOLUMNS(FILTER({V}, {V}[VipLevel]>=2 && {V}[SiteName] IN {{"Nova88","Goal123","Bwing"}}), "c",{V}[CustId], "v",{V}[VipLevel], "s",{V}[SiteName], "rg",{V}[RegTime_utc8])')
VM=f'TREATAS({{"Nova88","Goal123","Bwing"}},{V}[SiteName])'
LT=f'"dep",CALCULATE(SUM({V}[LT_Deposit])),"nd",CALCULATE(SUM({V}[LT_NetDeposit])),"wl",CALCULATE(SUM({V}[LT_WinLoss])),"bo",CALCULATE(SUM({V}[LT_Bonus])),"vb",CALCULATE(SUM({V}[LT_EffectiveBet]))'
LTs='"dep",[dep],"nd",[nd],"wl",[wl],"bo",[bo],"vb",[vb]'
KEY=f'"k",[k],"si",{V}[SiteName],"cu",{V}[CurrencyId],"v",{V}[VipLevel]'
SUMV=f'SUMMARIZE({V},{V}[SiteName],{V}[CurrencyId],{V}[VipLevel])'
Q['RM']=('PP','[k],[si],[cu],[v],[nru],[fdu],[fd7],[dep],[nd],[wl],[bo],[vb],[pad]',
  f'DEFINE VAR M = {dtab(months(14))}\nEVALUATE SELECTCOLUMNS(GENERATE(M, VAR s=[s] VAR e=[e] RETURN CALCULATETABLE(ADDCOLUMNS({SUMV},"nru",CALCULATE(COUNTROWS({V})),"fdu",CALCULATE(COUNTROWS({V}),NOT ISBLANK({V}[FirstDepositDate_utc8])),"fd7",CALCULATE(COUNTROWS(FILTER({V},NOT ISBLANK({V}[FirstDepositDate_utc8]) && {V}[FirstDepositDate_utc8]<{V}[RegTime_utc8]+7))),{LT}), {V}[RegTime_utc8]>=s, {V}[RegTime_utc8]<e, {VM})), {KEY},"nru",[nru],"fdu",[fdu],"fd7",[fd7],{LTs},{PAD})')
FB=f'"fdu",CALCULATE(COUNTROWS({V})),"new",CALCULATE(COUNTROWS({V}),{V}[RegTime_utc8]>=s),"one",CALCULATE(COUNTROWS({V}),{V}[LT_DepositCnt]<=1),{LT}'
FBs='"fdu",[fdu],"new",[new],"one",[one],'+LTs
Q['FM']=('PP','[k],[si],[cu],[v],[fdu],[new],[one],[dep],[nd],[wl],[bo],[vb],[pad]',
  f'DEFINE VAR M = {dtab(months(14))}\nEVALUATE SELECTCOLUMNS(GENERATE(M, VAR s=[s] VAR e=[e] RETURN CALCULATETABLE(ADDCOLUMNS({SUMV},{FB}), {V}[FirstDepositDate_utc8]>=s, {V}[FirstDepositDate_utc8]<e, {VM})), {KEY},{FBs},{PAD})')
Q['FD_daily']=('PP','[k],[si],[cu],[v],[fdu],[new],[one],[dep],[nd],[wl],[bo],[vb]',
  f'DEFINE VAR M = SELECTCOLUMNS(CALENDAR(dt"2026-07-01",{d(D)}),"k",FORMAT([Date],"yyyy-mm-dd"),"s",[Date],"e",[Date]+1)\nEVALUATE SELECTCOLUMNS(GENERATE(M, VAR s=[s] VAR e=[e] RETURN CALCULATETABLE(ADDCOLUMNS({SUMV},{FB}), {V}[FirstDepositDate_utc8]>=s, {V}[FirstDepositDate_utc8]<e, {VM})), {KEY},{FBs})')
Q['base']=('PP','view[SiteName],view[Currency],view[VipLevel],[n],[t],[pad]   (drop rows where n blank)',
  f'EVALUATE SUMMARIZECOLUMNS({V}[SiteName],{V}[Currency],{V}[VipLevel], {VM}, "n", COUNTROWS({V}), "t", CALCULATE(COUNTROWS({V}),{V}[IsTest]=TRUE()), {PAD})')
Q['_missmap_TEMPLATE']=('PP','[c],[mg],[mc],[ac],[an],[pad]   replace {IDS} with the ids in rNN/miss.txt (comma separated)',
  f'EVALUATE CALCULATETABLE(SELECTCOLUMNS({V}, "c",{V}[CustId], "mg",{V}[MarketingGroup], "mc",{V}[MarketingChannel], "ac",{V}[AffCode], "an",{V}[AffiliateName], {PAD}), {V}[CustId] IN {{{{IDS}}}})')
for n,t in (('_schema_PP','view_CustomerProfile'),('_schema_MK_acq','Acquisition Report Consolidate New'),('_schema_MK_master','Acquisition Master Channel List'),('_schema_PP_tags','CustTagSummary')):
    Q[n]=('PP' if 'PP' in n else 'MK','[t],[c]',f'EVALUATE FILTER(SELECTCOLUMNS(INFO.VIEW.COLUMNS(), "t", [Table], "c", [Name]), [t]="{t}")')
os.makedirs('queries',exist_ok=True)
for f in os.listdir('queries'): os.remove('queries/'+f)
conn={'MK':'AI Report_Marketing (workspace B2C-AI)','PR':'AI Report_Product (workspace B2C-AI)','PP':'Player Profile 360 (workspace B2C-Player Profile)'}
with open('queries/INDEX.txt','w') as ix:
    ix.write(f'Queries for D={D}  CUT={CUT}\n\n')
    for n,(c,h,q) in Q.items():
        open(f'queries/{n}.dax','w').write(q+'\n'); ix.write(f'{n:18s} {c}  {conn[c]}\n   expected header: {h}\n')
print(len(Q),'queries written to queries/ for',D)
