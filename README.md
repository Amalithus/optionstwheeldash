# Premium Desk — self-hosted
Weekly-options screening dashboard, rebuilt 3× each U.S. trading day (morning / midday / late session, ET) by GitHub Actions and published to GitHub Pages at https://amalithus.github.io/optionstwheeldash/.
To refresh manually: Actions tab -> Build Premium Desk -> Run workflow.

## Universe
Loads the **full S&P 500** plus any tickers you list in **extra_tickers.txt** (your custom non-S&P watchlist). Downside-safety scores are benchmarked across the whole combined universe (~510 names). "Weeklies only" and the price cap are **UI filters** on the page — they no longer cut the universe, so every name is scored and one toggle away from view.

## Editing your custom list
Open **extra_tickers.txt**, add/remove tickers (one per line, `#` for comments), commit, then Actions -> Run workflow.

## Files
- `screen_data.py` — data pipeline (universe, Yahoo pull, earnings, scoring).
- `extra_tickers.txt` — your custom non-S&P tickers to also pull.
- `premium_desk_template.html` — page shell with the `__DATA__` placeholder.
- `build_site.py` — writes `site/index.html` (light) + `site/charts/<SYM>.json` (per-name 6-month chart series, fetched lazily on row-expand).
- `.github/workflows/build.yml` — schedule + deploy.

Run locally: `pip install -r requirements.txt && python build_site.py`
