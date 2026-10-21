# Local development

The visitor entrypoint is `app.py`. Python **3.12** is the documented working runtime for local reproduction and Streamlit Community Cloud. The application works without model API credentials, private source archives, or dataset downloads.

## Set up the existing application

```bash
git clone https://github.com/ryandej/csusb-cyber-ai-research.git
cd csusb-cyber-ai-research
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate`.

For tests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

[VERIFICATION.md](../VERIFICATION.md) documents the Chromium installation and regression commands. [DEPLOYMENT.md](../DEPLOYMENT.md) covers the live application, hosted configuration, and optional server-side email secret. Never commit a real contact address, `.streamlit/secrets.toml`, or credentials.

## Runtime layout

| Path | Responsibility |
| --- | --- |
| `app.py` | Streamlit entrypoint and browser title. |
| `src/context_safety/ui/` | Accepted dashboard rendering, styles, interactions, and contact handling. |
| `src/context_safety/demonstration/` | Strict display contracts, historical validators, approved-release loader, and Research references. |
| `data/approved/v0.4.1/` | Exact approved display JSON and immutable historical About copy. |
| `data/presentation/2026-10-21/about.md` | Owner-approved current About copy, validated with its own SHA-256 pin. |
| `tests/` and `scripts/` | Content preservation, fail-closed loading, evidence coverage, privacy, and browser regressions. |

The approved fixture retains its historical private-review metadata. Public-display authorization applies externally to the exact pinned bytes, not to editable status flags. The original historical source-validation path remains available for private development; the deployed viewer uses only the pinned approved fixture. Raw transcripts, private review archives, secrets, and the separate developer evaluation interface are not shipped.

## Scope of the presentation update

The October 21, 2026 presentation release changes the dashboard title/subtitle, Streamlit page title, and displayed About copy. Narrow preservation tests distinguish these authorized revisions from the historical baseline and reject other changes. The source records, case analysis, proposed responses, Contact functionality, application architecture, and dependencies remain unchanged. The research architecture and roadmap describe future work, not installed functionality.

Keep screenshot capture outputs and review reports in ignored `local-artifacts/` directories. Only reviewed, email-free README images belong in `docs/images/readme/`. The historical `docs/images/dashboard.png` remains as the accepted v0.4.1 visual baseline.
