#!/usr/bin/env python3
"""Premium Desk — self-contained data pipeline. Outputs dashboard_data.json.
All sources are public & cloud-reachable (no desktop/IBKR needed)."""
import urllib.request, urllib.parse, http.cookiejar, json, time, math, statistics, datetime, re, sys
import pandas as pd, io
from collections import defaultdict
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
NUA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)','Accept':'application/json'}

# ---- Yahoo crumb session ----
_op=None;_crumb=None
def session():
    global _op,_crumb
    if _op:return _op,_crumb
    cj=http.cookiejar.CookieJar();_op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:_op.open(urllib.request.Request('https://fc.yahoo.com',headers=UA),timeout=10)
    except:pass
    _crumb=_op.open(urllib.request.Request('https://query1.finance.yahoo.com/v1/test/getcrumb',headers=UA),timeout=10).read().decode()
    return _op,_crumb
def jget(url,tries=3):
    op,_=session()
    for i in range(tries):
        try:return json.loads(op.open(urllib.request.Request(url,headers=UA),timeout=25).read())
        except Exception as e:
            if i==tries-1:raise
            time.sleep(1.3*(i+1))
def val(d,k):
    v=d.get(k) if isinstance(d,dict) else None
    return v.get('raw') if isinstance(v,dict) else v

def build_universe():
    html=urllib.request.urlopen(urllib.request.Request('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',headers=UA),timeout=30).read().decode()
    df=pd.read_html(io.StringIO(html))[0]
    syms=df['Symbol'].astype(str).str.replace('.','-',regex=False).str.strip().tolist()
    sectors=dict(zip(syms,df['GICS Sector'].astype(str)))
    wk=urllib.request.urlopen(urllib.request.Request('https://www.cboe.com/available_weeklys/get_csv_download/',headers=UA),timeout=25).read().decode()
    lines=wk.splitlines();start=[i for i,l in enumerate(lines) if 'Available Weeklys - Equity' in l][0]
    weeklys=set()
    for l in lines[start+1:]:
        m=re.match(r'"([A-Z][A-Z\.\-]{0,6})",',l)
        if m:weeklys.add(m.group(1).replace('.','-'))
    cand=sorted(set(syms)&weeklys)
    # bulk quote to filter price<120
    op,cr=session();elig=[]
    for i in range(0,len(cand),60):
        b=cand[i:i+60]
        try:
            j=jget('https://query1.finance.yahoo.com/v7/finance/quote?symbols='+urllib.parse.quote(','.join(b))+'&crumb='+urllib.parse.quote(cr))
            for r in j.get('quoteResponse',{}).get('result',[]):
                p=r.get('regularMarketPrice')
                if p is not None and p<120:elig.append(r['symbol'])
        except Exception as e:print('quote batch fail',e,file=sys.stderr)
        time.sleep(0.4)
    return elig,sectors

def pull(elig,sectors):
    MODS='financialData,defaultKeyStatistics,summaryDetail,calendarEvents,price,earningsHistory'
    op,cr=session();data={}
    w={'strongBuy':1,'buy':2,'hold':3,'sell':4,'strongSell':5}
    for i,s in enumerate(elig):
        r={'symbol':s,'sector':sectors.get(s,'Unknown')}
        try:
            j=jget(f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{urllib.parse.quote(s)}?modules={MODS}&crumb='+urllib.parse.quote(cr))['quoteSummary']['result'][0]
            fd=j.get('financialData',{});ks=j.get('defaultKeyStatistics',{});sd=j.get('summaryDetail',{});ce=j.get('calendarEvents',{});pr=j.get('price',{});eh=j.get('earningsHistory',{})
            r['name']=val(pr,'longName') or val(pr,'shortName') or s
            r['price']=val(fd,'currentPrice') or val(pr,'regularMarketPrice')
            r['recMean']=val(fd,'recommendationMean');r['recKey']=fd.get('recommendationKey');r['numAnalysts']=val(fd,'numberOfAnalystOpinions')
            r['targetMean']=val(fd,'targetMeanPrice');r['targetHigh']=val(fd,'targetHighPrice');r['targetLow']=val(fd,'targetLowPrice')
            r['debtToEquity']=val(fd,'debtToEquity');r['currentRatio']=val(fd,'currentRatio');r['quickRatio']=val(fd,'quickRatio')
            r['totalDebt']=val(fd,'totalDebt');r['totalCash']=val(fd,'totalCash');r['ebitda']=val(fd,'ebitda')
            r['profitMargins']=val(fd,'profitMargins');r['operatingMargins']=val(fd,'operatingMargins');r['grossMargins']=val(fd,'grossMargins')
            r['roe']=val(fd,'returnOnEquity');r['roa']=val(fd,'returnOnAssets');r['revenueGrowth']=val(fd,'revenueGrowth');r['earningsGrowth']=val(fd,'earningsGrowth');r['fcf']=val(fd,'freeCashflow')
            r['trailingPE']=val(sd,'trailingPE') or val(ks,'trailingPE');r['forwardPE']=val(sd,'forwardPE') or val(ks,'forwardPE')
            r['beta']=val(ks,'beta') or val(sd,'beta');r['divYield']=val(sd,'dividendYield');r['marketCap']=val(pr,'marketCap')
            r['payoutRatio']=val(sd,'payoutRatio');r['exDivDate']=val(sd,'exDividendDate')
            ed=ce.get('earnings',{}).get('earningsDate') if ce else None
            r['earningsDate']=ed[0].get('raw') if ed and isinstance(ed,list) and ed else None
            if r.get('recMean') is None:
                try:
                    tr=jget(f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{s}?modules=recommendationTrend&crumb='+urllib.parse.quote(cr))['quoteSummary']['result'][0]['recommendationTrend']['trend']
                    if tr:
                        cu=tr[0];n=sum(cu.get(k,0) for k in w)
                        if n:r['recMean']=round(sum(cu.get(k,0)*v for k,v in w.items())/n,2)
                except:pass
        except Exception as e:r['err_qs']=str(e)[:80]
        try:
            c=jget(f'https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(s)}?range=1y&interval=1d')['chart']['result'][0]
            cl=[x for x in c['indicators']['quote'][0]['close'] if x is not None]
            if len(cl)>30:
                rets=[math.log(cl[k]/cl[k-1]) for k in range(1,len(cl)) if cl[k-1]]
                r63=rets[-63:] if len(rets)>=63 else rets
                r['histVol']=statistics.pstdev(r63)*math.sqrt(252) if len(r63)>2 else None
                ma50=sum(cl[-50:])/min(50,len(cl));ma200=sum(cl[-200:])/min(200,len(cl))
                r['ma50']=ma50;r['ma200']=ma200;r['distMA50']=cl[-1]/ma50-1;r['distMA200']=cl[-1]/ma200-1
                hi=max(cl);lo=min(cl);r['pos52w']=(cl[-1]-lo)/(hi-lo) if hi>lo else None
                r['ret1m']=(cl[-1]/cl[-21]-1) if len(cl)>21 else None;r['ret3m']=(cl[-1]/cl[-63]-1) if len(cl)>63 else None
                peak=cl[0];mdd=0
                for x in cl:peak=max(peak,x);mdd=min(mdd,x/peak-1)
                r['maxDD1y']=mdd
                simple=[cl[k]/cl[k-1]-1 for k in range(1,len(cl)) if cl[k-1]]
                downs=[x for x in simple if x<0]
                r['downsideDev']=statistics.pstdev(downs)*math.sqrt(252) if len(downs)>2 else None
                r['worstDrop1d']=min(simple) if simple else None
                r['gapDays']=sum(1 for x in simple if x<=-0.05)
                if len(simple)>10:
                    mm=statistics.fmean(simple);ss=statistics.pstdev(simple)
                    r['retSkew']=(sum((x-mm)**3 for x in simple)/len(simple)/(ss**3)) if ss>0 else None
        except Exception as e:r['err_ch']=str(e)[:80]
        data[s]=r
        time.sleep(0.22)
    return data

def nasdaq_earnings(today,days=22):
    nas={};d=today
    for _ in range(days):
        if d.weekday()<5:
            try:
                j=json.loads(urllib.request.urlopen(urllib.request.Request(f'https://api.nasdaq.com/api/calendar/earnings?date={d.isoformat()}',headers=NUA),timeout=20).read())
                for row in (j.get('data') or {}).get('rows') or []:nas[row['symbol']]=d.isoformat()
            except:pass
            time.sleep(0.3)
        d+=datetime.timedelta(days=1)
    return nas

def pct_rank(xs,v,hib=True):
    xs=[x for x in xs if x is not None]
    if v is None or not xs:return None
    below=sum(1 for x in xs if x<v);eq=sum(1 for x in xs if x==v)
    p=(below+0.5*eq)/len(xs)*100
    return p if hib else 100-p

def N(x):return 0.5*(1+math.erf(x/math.sqrt(2)))
def bs(S,K,T,sig,r,call=True):
    if sig<=0 or T<=0:return 0.0
    d1=(math.log(S/K)+(r+sig*sig/2)*T)/(sig*math.sqrt(T));d2=d1-sig*math.sqrt(T)
    return S*N(d1)-K*math.exp(-r*T)*N(d2) if call else K*math.exp(-r*T)*N(-d2)-S*N(-d1)
def ninv(p):
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00];pl=0.02425
    if p<pl:q=math.sqrt(-2*math.log(p));return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p<=1-pl:q=p-0.5;r2=q*q;return (((((a[0]*r2+a[1])*r2+a[2])*r2+a[3])*r2+a[4])*r2+a[5])*q/(((((b[0]*r2+b[1])*r2+b[2])*r2+b[3])*r2+b[4])*r2+1)
    q=math.sqrt(-2*math.log(1-p));return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

def score_and_premium(data,nas,today):
    rows=list(data.values())
    friday=today+datetime.timedelta((4-today.weekday())%7)
    for r in rows:
        td,tc,eb=r.get('totalDebt'),r.get('totalCash'),r.get('ebitda')
        r['netDebtEbitda']=((td-tc)/eb) if (td is not None and tc is not None and eb and eb>0) else None
    A={k:[r.get(k) for r in rows] for k in ['debtToEquity','netDebtEbitda','currentRatio','profitMargins','operatingMargins','roe','beta','histVol','maxDD1y','downsideDev','worstDrop1d','recMean','trailingPE']}
    secPE=defaultdict(list)
    for r in rows:
        pe=r.get('trailingPE')
        if pe and pe>0:secPE[r['sector']].append(pe)
    secMed={s:statistics.median(v) for s,v in secPE.items() if len(v)>=3}
    for r in rows:
        q=[pct_rank(A['debtToEquity'],r.get('debtToEquity'),False),pct_rank(A['netDebtEbitda'],r.get('netDebtEbitda'),False),
           pct_rank(A['currentRatio'],r.get('currentRatio'),True),pct_rank(A['profitMargins'],r.get('profitMargins'),True),
           pct_rank(A['operatingMargins'],r.get('operatingMargins'),True),pct_rank(A['roe'],r.get('roe'),True)]
        fcf=r.get('fcf');q.append(70 if (fcf and fcf>0) else (30 if fcf is not None else None))
        qv=[x for x in q if x is not None];r['scoreFund']=round(sum(qv)/len(qv),1) if qv else 50.0
        v=[pct_rank(A['beta'],r.get('beta'),False),pct_rank(A['histVol'],r.get('histVol'),False),pct_rank(A['maxDD1y'],r.get('maxDD1y'),True),pct_rank(A['downsideDev'],r.get('downsideDev'),False),pct_rank(A['worstDrop1d'],r.get('worstDrop1d'),True)]
        d200=r.get('distMA200');v.append(65 if (d200 is not None and d200>=0) else (35 if d200 is not None else None))
        vv=[x for x in v if x is not None];r['scoreVol']=round(sum(vv)/len(vv),1) if vv else 50.0
        a=[pct_rank(A['recMean'],r.get('recMean'),False)]
        tm,pr=r.get('targetMean'),r.get('price')
        if tm and pr:
            up=tm/pr-1;a.append(max(0,min(100,50+up*150)) if up<0.6 else 55)
        av=[x for x in a if x is not None];r['scoreAnalyst']=round(sum(av)/len(av),1) if av else 50.0
        pe=r.get('trailingPE');med=secMed.get(r['sector'])
        if pe and pe>0 and med:r['scoreVal']=round(max(0,min(100,100-(pe/med-1)*60-max(0,pe-40)*0.5)),1)
        elif pe and pe>0:r['scoreVal']=round(pct_rank([x for x in A['trailingPE'] if x and x>0],pe,False),1)
        else:r['scoreVal']=35.0
        r['composite']=round(0.35*r['scoreFund']+0.30*r['scoreVol']+0.20*r['scoreAnalyst']+0.15*r['scoreVal'],1)
        # earnings gate (Yahoo + Nasdaq override)
        ed=r.get('earningsDate');r['earningsDateStr']=None;r['daysToEarnings']=None;r['earnBeforeExpiry']=False;r['earnThisWeek']=False
        if ed:
            edate=datetime.datetime.utcfromtimestamp(ed).date();r['earningsDateStr']=edate.isoformat();r['daysToEarnings']=(edate-today).days
        nd=nas.get(r['symbol']);r['nasdaqEarnings']=nd
        if nd:
            nde=datetime.date.fromisoformat(nd);dte=(nde-today).days
            if r['daysToEarnings'] is None or r['daysToEarnings']<0 or r['earningsDateStr'] is None:
                r['earningsDateStr']=nd;r['daysToEarnings']=dte
        if r['earningsDateStr']:
            e=datetime.date.fromisoformat(r['earningsDateStr']);dte=(e-today).days
            r['earnThisWeek']=bool(0<=dte<=6);r['earnBeforeExpiry']=bool(today<=e<=friday)
        r['exDivDateStr']=None;r['exDivBeforeExpiry']=False
        ex=r.get('exDivDate')
        if ex:
            try:
                exd=datetime.datetime.utcfromtimestamp(ex).date()
                if exd>=today:  # only surface UPCOMING ex-div; Yahoo often returns a stale past one
                    r['exDivDateStr']=exd.isoformat();r['exDivBeforeExpiry']=bool(exd<=friday)
            except:pass
        # premium (BS on realized vol, ~0.15 delta, 1wk)
        S=r.get('price');sig=r.get('histVol');r['estWeekPremPct']=None;r['annPremYield']=None
        if S and sig and sig>0:
            T=7/365;rr=0.043
            cK=S/math.exp(ninv(0.15)*sig*math.sqrt(T)-(rr+sig*sig/2)*T)
            pK=S/math.exp(-ninv(0.15)*sig*math.sqrt(T)-(rr+sig*sig/2)*T)
            cP=bs(S,cK,T,sig,rr,True);pP=bs(S,pK,T,sig,rr,False);wk=((cP+pP)/2)/S*100   # single-leg average (user sells one side only)
            r['callStrike']=round(cK,1);r['putStrike']=round(pK,1);r['callPrem']=round(cP,2);r['putPrem']=round(pP,2)
            r['estWeekPremPct']=round(wk,2);r['annPremYield']=round(wk*52,1)
    rows.sort(key=lambda r:-r['composite'])
    return rows,friday

def main():
    today=datetime.date.today()
    print('universe...',file=sys.stderr);elig,sectors=build_universe();print(f'  {len(elig)} eligible',file=sys.stderr)
    print('pulling data...',file=sys.stderr);data=pull(elig,sectors)
    print('nasdaq earnings...',file=sys.stderr);nas=nasdaq_earnings(today)
    print('scoring...',file=sys.stderr);rows,friday=score_and_premium(data,nas,today)
    keep=['symbol','name','sector','price','composite','scoreFund','scoreVol','scoreAnalyst','scoreVal','beta','histVol','maxDD1y','distMA50','distMA200','pos52w','ret1m','ret3m','debtToEquity','netDebtEbitda','currentRatio','profitMargins','operatingMargins','roe','fcf','trailingPE','forwardPE','divYield','marketCap','recMean','recKey','numAnalysts','targetMean','targetHigh','targetLow','earningsDateStr','daysToEarnings','earnBeforeExpiry','earnThisWeek','nasdaqEarnings','callStrike','putStrike','callPrem','putPrem','estWeekPremPct','annPremYield','downsideDev','worstDrop1d','gapDays','retSkew','payoutRatio','exDivDateStr','exDivBeforeExpiry']
    out=[{k:r.get(k) for k in keep} for r in rows]
    meta={'generated':datetime.datetime.utcnow().isoformat()+'Z','asOfDate':today.isoformat(),'expiryFriday':friday.isoformat(),'universeCount':len(out),'filters':'S&P 500 constituent | has weekly options (Cboe) | price < $120'}
    json.dump({'meta':meta,'rows':out},open('dashboard_data.json','w'),default=str)
    print(f'OK {len(out)} names, {sum(1 for r in out if r["earnBeforeExpiry"])} benched, expiry {friday}',file=sys.stderr)

if __name__=='__main__':main()
