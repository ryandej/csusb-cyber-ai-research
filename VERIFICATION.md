# Release verification

The public runtime retains the original owner-approved redacted display fixture and historical About copy without regeneration. The October 21 presentation release displays a separately approved, versioned About file:

| File | SHA-256 |
| --- | --- |
| `data/approved/v0.4.1/preview.json` | `ac89e0da1c64d15f677bf52da5fd9af5e6b2da997b613f0d2434981cf9aae5db` |
| `data/approved/v0.4.1/about.md` | `891b20f6aa78bf6f75831e8b48ef6bbdb7bffa564caab4f8e638df00159c9976` |
| `data/presentation/2026-10-21/about.md` | `14e4cd9a456fc5efb3a258284b5a12d4470d45a22116924d4901de3d5669bbe1` |

The release loader checks the display-file digest before using the original schema and rendered evidence-coverage validation. The About renderer validates the current file against its explicit digest pin. A changed file fails closed; a new manifest or altered publication status cannot authorize it. The historical full source-verification loader remains intact but is not needed by the packaged release.

`tests/original-render-fingerprints.json` records the original locally source-validated catalog, complete browser payload, About/Research HTML, and unchanged entrypoint, contracts, renderers, styles, and scripts. Tests compare strict serialization and SHA-256, including whitespace. The three protected responses are also checked by the original schema. These are software-preservation checks, not empirical AI evaluations.

## October 21, 2026 presentation amendment

The historical fingerprint file and approved display data remain unchanged. The owner authorized exactly three substitutions:

| Location | Original | Authorized replacement |
| --- | --- | --- |
| `app.py` page title | `Context-Aware AI Safety` | `Context-Aware LLM Safety Classifier` |
| `review.js` dashboard heading | `Context-Aware AI Safety` | `Context-Aware LLM Safety Classifier` |
| `review.js` dashboard subtitle | `Cybersecurity assistance, risk, and utility` | `Reducing unnecessary refusals while maintaining safeguards against harmful assistance.` |

The same release replaces the displayed About content with the owner's exact Overview, Demonstration, and Author paragraphs. The About navigation label and Contact section remain unchanged. `review_app.py` changes only the About file path and digest pin; the renderer and contact behavior remain intact. The historical file remains at `data/approved/v0.4.1/about.md` and is not used as a fallback for invalid current content.

`tests/test_exact_release.py` requires each exact authorized literal once, rejects the old literal, and reverses only the three header substitutions and two About path/pin substitutions in memory before comparing original SHA-256 values. The original `review_app.py` hash is explicitly pinned alongside the unchanged historical fingerprint manifest. Additional code, whitespace changes, duplicate literals, missing replacements, and different values remain detectable. Negative tests exercise those cases. All other protected files retain their original byte comparisons. The historical baseline has not been regenerated or retroactively relabeled.

Separate tests verify the historical About bytes and rendered HTML against their original fingerprints, and the current About bytes and HTML against new explicit pins. They also require the Contact source and rendered section to match the historical version exactly. Browser and unit tests check the current section order, exact copy, absence of descriptive bold emphasis, and fail-closed rejection of missing, changed, historical, or resealed replacement content. All source/evidence/privacy protections remain in place.

The Chromium regression asserts the updated heading, subtitle, and Overview page. Its existing case, evidence, privacy, accessibility, and layout checks remain intact. The README walkthrough uses captures from the updated dashboard. Its response-analysis crop uses the original captured pixels and links to the complete image. The original `docs/images/dashboard.png` remains a historical visual control.

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
