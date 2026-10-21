# Deploy the accepted dashboard

The entrypoint is **`app.py`**, using the existing v0.4.1 interface and the exact approved display files. No model backend, data download, raw transcript, or private review archive is required.

Live application: **https://context-aware-ai-safety.streamlit.app/**

## Streamlit Community Cloud

Sign in at [Streamlit Community Cloud](https://share.streamlit.io/) with the GitHub account that can connect this repository. Choose **Create app**, then **Yup, I have an app**.

| Setting | Value |
| --- | --- |
| Repository | `ryandej/csusb-cyber-ai-research` |
| Branch | `main` |
| Main file path | `app.py` |
| Advanced settings → Python | `3.12` |

The existing deployment uses the live URL above. Preserve the repository, `main` branch, and `app.py` entrypoint when maintaining it. Cloud installs `requirements.txt`; its constraints preserve the accepted Streamlit/Pydantic versions. The configuration keeps the accepted dark theme, disables usage statistics and static-directory serving, and permits the hosting platform to choose its listening interface.

The October 21 presentation release updates the project header and displayed About copy while preserving the case content and application behavior. After updates to `main`, verify the hosted title, subtitle, Overview page, and unchanged case content. Keep `app.py` as the single public entrypoint.

The accepted configuration sets `server.fileWatcherType = "none"`. After publishing Python changes, [reboot the app from Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/reboot-your-app) to load the updated Python code. A file-read JavaScript header can update while the running process still serves older Python code, so check the browser title and About copy as well as the visible dashboard heading. Reboot requires signing in to the app's Streamlit workspace.

See the official [deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [dependency documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

## Optional email contact

Only the owner enters the real contact address in **Advanced settings → Secrets**, or later in the app's secrets settings:

```toml
[contact]
email = "your-address@example.com"
```

The example is a placeholder. Never commit a real address or `.streamlit/secrets.toml`. For local operation, the existing `CONTACT_EMAIL` environment variable is also supported and takes precedence over the secrets file. An explicitly empty variable disables the contact address.

The address stays server-side until the visitor activates **Reveal email**. Copy and Hide then use the accepted interface. Navigation and fresh sessions clear the revealed state. No `mailto:` link is created. With no configured contact address, the app remains usable and reports contact availability through its existing controls. This interaction limits incidental exposure; it is not authentication or a guarantee against scraping after Reveal.

See [Streamlit secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Verify hosted updates

After an authorized update, open https://context-aware-ai-safety.streamlit.app/ in a fresh browser and check:

1. The original three case choices, source turn IDs, redactions, and full conversation display.
2. Passage/explanation links in both directions, expansion, collapsed evidence groups, and Observation mode.
3. Scenario summary, exact proposed response and target, reasoning, and training application.
4. All seven Research references and the About tab's Overview, Demonstration, Author, and Contact sections.
5. Desktop and 390/320-pixel mobile layouts, keyboard controls, and contact Reveal/Copy/Hide.
6. No missing-content placeholders or dependency errors.

Compare the research content and interface with `docs/images/dashboard.png` and the owner's accepted screenshots, accounting for the authorized header and About-copy revisions. The five walkthrough captures in `docs/images/readme/` show the updated application; the response-analysis image also has a focused inline crop. Confirm the browser title and check the heading/subtitle for clipping at desktop, 390-pixel, and 320-pixel widths. Keep real contact-email Reveal captures out of public documentation.
