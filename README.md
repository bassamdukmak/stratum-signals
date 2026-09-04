# stratum-signals

Public read-only snapshot of the Stratum signal dashboard (`index.html`, served by GitHub Pages). No credentials are in the page: every Supabase read is short-circuited by an embedded `SNAPSHOT` object.
Rebuilt nightly by `.github/workflows/rebuild.yml` (22:30 UTC, after the 17:00 ET grader): `build/build.py` captures the rows via `build/capture.py`, substitutes them into `template.html`, and commits `index.html` if it changed.
Run locally: `SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python3 build/build.py` (Python 3.12 stdlib only).
Force a rebuild: Actions -> Rebuild -> Run workflow.
Edit the page in `template.html`, never in `index.html`; the build fails if the output is missing a table or contains a key.
