#!/usr/bin/env python3
"""Build Premium Desk into ./site/index.html for GitHub Pages."""
import os, json, datetime
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
import screen_data
today=datetime.date.today()
elig,sectors=screen_data.build_universe()
data=screen_data.pull(elig,sectors)
nas=screen_data.nasdaq_earnings(today)
rows,friday=screen_data.score_and_premium(data,nas,today)
keep=['symbol','name','sector','price','composite','scoreFund','scoreVol','scoreAnalyst','scoreVal','beta','histVol','maxDD1y','distMA50','distMA200','pos52w','ret1m','ret3m','debtToEquity','netDebtEbitda','currentRatio','profitMargins','operatingMargins','roe','fcf','trailingPE','forwardPE','divYield','marketCap','recMean','recKey','numAnalysts','targetMean','targetHigh','targetLow','earningsDateStr','daysToEarnings','earnBeforeExpiry','earnThisWeek','nasdaqEarnings','callStrike','putStrike','callPrem','putPrem','estWeekPremPct','annPremYield','downsideDev','worstDrop1d','gapDays','retSkew','payoutRatio','exDivDateStr','exDivBeforeExpiry','bbLower','bbMid','bbUpper']
out=[{k:r.get(k) for k in keep} for r in rows]
meta={'generated':datetime.datetime.utcnow().isoformat()+'Z','asOfDate':today.isoformat(),'expiryFriday':friday.isoformat(),'universeCount':len(out),'filters':'S&P 500 constituent | has weekly options (Cboe) | price < $120'}
payload={'meta':meta,'rows':out}
os.makedirs('site',exist_ok=True)
final=open('premium_desk_template.html').read().replace('__DATA__', json.dumps(payload,default=str))
assert '__DATA__' not in final
# Wrap as a full standards-mode document (standalone page needs its own doctype; the Artifact tool adds its own, this path does not)
final='<!doctype html>\n<html lang="en">\n'+final+'\n</html>\n'
open('site/index.html','w').write(final)
print(f'BUILT site/index.html — {len(out)} names, {len(final)} bytes')
