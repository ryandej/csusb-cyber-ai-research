# Release verification

The public runtime packages the owner-approved redacted display fixture and About copy without regeneration:

| File | SHA-256 |
| --- | --- |
| `data/approved/v0.4.1/preview.json` | `ac89e0da1c64d15f677bf52da5fd9af5e6b2da997b613f0d2434981cf9aae5db` |
| `data/approved/v0.4.1/about.md` | `891b20f6aa78bf6f75831e8b48ef6bbdb7bffa564caab4f8e638df00159c9976` |

The release loader checks the display-file digest before using the original schema and rendered evidence-coverage validation. The About renderer retains its original digest check. A changed file fails closed; a new manifest or altered publication status cannot authorize it. The historical full source-verification loader remains intact but is not needed by the packaged release.

`tests/original-render-fingerprints.json` records the original locally source-validated catalog, complete browser payload, About/Research HTML, and unchanged entrypoint, contracts, renderers, styles, and scripts. Tests compare strict serialization and SHA-256, including whitespace. The three protected responses are also checked by the original schema. These are software-preservation checks, not empirical AI evaluations.

The original v0.4.1 unit and browser regressions were adapted only for packaged inputs and configurable test URLs/output directories. Historical source-replay tests run in the owner's original checkout; the public loader tests instead exercise the fixed approved digest and rejection of resealed modifications. Private source records and review archives are not test dependencies here.

## Unit tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Chromium regression

Install Chromium into a repository-local cache:

```bash
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright"
python -m playwright install chromium
```

Run two local app instances in separate terminals. Use only the fictional test address below for privacy checks:

```bash
CONTACT_EMAIL=review.contact@example.invalid python -m streamlit run app.py --server.address 127.0.0.1 --server.port 18517
```

```bash
CONTACT_EMAIL='' python -m streamlit run app.py --server.address 127.0.0.1 --server.port 18519
```

Then run the browser checks from the activated environment:

```bash
python scripts/outcome_walkthrough.py
CONTACT_EMAIL=review.contact@example.invalid python scripts/polish_walkthrough.py
```

The scripts block requests outside the configured local app URLs. `APP_URL`, `MISSING_CONTACT_URL`, and `REVIEW_OUTPUT` can override the localhost defaults and private output directory. Screenshots and JSON reports default to ignored `local-artifacts/release-verification/`. Reveal screenshots must remain private; do not run these scripts against a real contact secret or publish the resulting screenshots indiscriminately.

Checks cover all three cases, exact full display text, original turn IDs and proposed responses, expansion, bidirectional evidence, four effect colors, redactions, collapsed groups, source-linked lower panels, Research/About, desktop and mobile layout, keyboard and forced-color interactions, clipboard behavior, and server-to-browser contact disclosure. Actual email values are never needed for verification.
