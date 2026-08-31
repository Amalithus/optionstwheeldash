# Premium Desk — self-hosted
Weekly-options screening dashboard, rebuilt 3× each U.S. trading day (morning / midday / late session, ET) by GitHub Actions and published to GitHub Pages at https://amalithus.github.io/optionstwheeldash/.
To refresh manually: Actions tab -> Build Premium Desk -> Run workflow.
Files: screen_data.py (pipeline), premium_desk_template.html (shell with __DATA__), build_site.py (writes site/index.html), .github/workflows/build.yml.
Run locally: pip install -r requirements.txt && python build_site.py
