# Premium Desk — self-hosted

A weekly-options screening dashboard for low-downside S&P 500 names (< $120 with weekly options).
A GitHub Action rebuilds it every weekday at ~9:35 a.m. ET and publishes the single-page site to GitHub Pages.

## What runs
- `screen_data.py` — pulls the universe + fundamentals/analyst/earnings/ex-div data (public sources: Wikipedia, Cboe, Yahoo, Nasdaq), scores every name, models premiums.
- `premium_desk_template.html` — the dashboard shell (a `__DATA__` placeholder gets the fresh data injected).
- `build_site.py` — runs the pipeline and writes `site/index.html`.
- `.github/workflows/build.yml` — the schedule + Pages deploy.

## One-time setup (about 5 minutes)

1. **Create a new PUBLIC repo** on GitHub — e.g. `premium-desk` (empty, no README).

2. **Push these files** from this folder:
   ```bash
   git init
   git add .
   git commit -m "Premium Desk"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/premium-desk.git
   git push -u origin main
   ```

3. **Enable Pages via Actions:** repo → **Settings → Pages → Build and deployment → Source: “GitHub Actions.”**

4. **First build:** repo → **Actions** tab → “Build Premium Desk” → **Run workflow** (manual trigger). After it finishes, your site is live at:
   ```
   https://YOUR_USERNAME.github.io/premium-desk/
   ```

That’s it. From then on it rebuilds itself automatically each weekday at ~9:35 a.m. ET.

## Schedule
The workflow has two UTC cron triggers (13:35 and 14:35). Both fire year-round, but a DST-aware guard step lets **only the one that lands at 9 a.m. ET** actually build — so it stays at ~9:35 ET through daylight-saving changes. Runs Monday–Friday. (Market holidays rebuild harmlessly with the prior session's data.) You can always rebuild on demand with the **Run workflow** button.

To change the time, edit the two `cron:` lines in `.github/workflows/build.yml` (they're in UTC) and the `et.hour == 9` guard.

## Put it on your website
- **Easiest — iframe:** drop this into any page on your site:
  ```html
  <iframe src="https://YOUR_USERNAME.github.io/premium-desk/"
          style="width:100%;height:1400px;border:0;" title="Premium Desk"></iframe>
  ```
- **Subdomain (custom domain):** repo → Settings → Pages → Custom domain → e.g. `screener.yoursite.com`, then add the CNAME record your DNS provider needs. GitHub issues HTTPS automatically.

## Notes
- The **watchlist** is saved per visitor in their own browser (localStorage), so each person who opens the page keeps their own list.
- Data comes from free/unofficial endpoints (Yahoo/Cboe/Nasdaq). Fine for personal use; they can rate-limit or change format. If a build fails, re-run it — the previous published page stays up until a new build succeeds.
- Premium/IV figures are **model estimates** for screening; confirm live prices in your broker before trading.

## Run locally
```bash
pip install -r requirements.txt
python build_site.py     # writes site/index.html
```
