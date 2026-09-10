#!/usr/bin/env python3
"""Build Premium Desk into ./site/index.html for GitHub Pages.
Lazy charts: row data ships WITHOUT the 6-month chart arrays (keeps the main page light);
each name's chart series is written to ./site/charts/<SYM>.json and fetched on row-expand."""
import os, json, datetime
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
import screen_data
today=datetime.date.today()
elig,sectors,weeklys=screen_data.build_universe()
data=screen_data.pull(elig,sectors,weeklys)
nas=screen_data.nasdaq_earnings(today)
rows,friday=screen_data.score_and_premium(data,nas,today)
# Row keep list — everything EXCEPT the big chart arrays (chartPx/chartBbL/chartBbU are lazy-loaded).
keep=['symbol','name','sector','hasWeeklys','price','composite','scoreFund','scoreVol','scoreAnalyst','scoreVal','beta','histVol','maxDD1y','distMA50','distMA200','pos52w','ret1m','ret3m','debtToEquity','netDebtEbitda','currentRatio','profitMargins','operatingMargins','roe','fcf','trailingPE','forwardPE','divYield','marketCap','recMean','recKey','numAnalysts','targetMean','targetHigh','targetLow','earningsDateStr','daysToEarnings','earnBeforeExpiry','earnThisWeek','nasdaqEarnings','callStrike','putStrike','callPrem','putPrem','estWeekPremPct','annPremYield','downsideDev','worstDrop1d','gapDays','retSkew','payoutRatio','exDivDateStr','exDivBeforeExpiry','bbLower','bbMid','bbUpper','dayChg']
out=[{k:r.get(k) for k in keep} for r in rows]
meta={'generated':datetime.datetime.utcnow().isoformat()+'Z','asOfDate':today.isoformat(),'expiryFriday':friday.isoformat(),'universeCount':len(out),'filters':'S&P 500 + custom extras | weeklies & price cap = UI filters','lazyCharts':True}
payload={'meta':meta,'rows':out}
os.makedirs('site/charts',exist_ok=True)
# Per-ticker chart sidecar files (only when we have a series)
nch=0
for r in rows:
    if r.get('chartPx'):
        json.dump({'px':r['chartPx'],'l':r.get('chartBbL'),'u':r.get('chartBbU')},
                  open(f"site/charts/{r['symbol']}.json",'w'),default=str)
        nch+=1
final=open('premium_desk_template.html').read().replace('__DATA__', json.dumps(payload,default=str))
assert '__DATA__' not in final
# Wrap as a full standards-mode document (own doctype + charset for correctness).
final='<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'+final+'\n</html>\n'
open('site/index.html','w').write(final)
print(f'BUILT site/index.html — {len(out)} names, {nch} chart files, {len(final)} bytes main')
