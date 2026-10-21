"""Private source-backed review surface, with dedicated Research and About views."""
from html import escape
from pathlib import Path
import streamlit as st

from context_safety.demonstration.polish_preview import load_polish_preview, load_approved_release
from context_safety.storage.provenance import sha256
from context_safety.ui.review_markup import inline
from context_safety.ui.contact import contact_payload
from context_safety.demonstration.research import REFERENCES
from context_safety.ui.outcome_markup import browser_case

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PACKAGED = ROOT / 'data/approved/v0.4.1'
USE_APPROVED_RELEASE = PACKAGED.is_dir()
DISPLAY = PACKAGED if USE_APPROVED_RELEASE else ROOT / 'local-artifacts/v0.4.1-owner-review'
PREVIEW = DISPLAY / 'preview.json'
BASELINE = ROOT / 'local-artifacts/v0.3.1-owner-review/preview.json'
SOURCE = ROOT / 'local-artifacts/CYB-386-Direct-e34d5d6e-4fb4-4b2c-8129-91ca3837ee33/CYB-386-Direct-e34d5d6e-4fb4-4b2c-8129-91ca3837ee33.md'
VIEWS = ('Demonstration', 'Research', 'About')

ABOUT_PIN = '891b20f6aa78bf6f75831e8b48ef6bbdb7bffa564caab4f8e638df00159c9976'
ABOUT = DISPLAY / 'about.md'


def load_catalog():
    # Never fall back to another dataset if packaged content fails validation.
    if USE_APPROVED_RELEASE:
        return load_approved_release(PREVIEW)
    return load_polish_preview(PREVIEW, BASELINE, SOURCE)


def about_markup():
    try:
        body = ABOUT.read_bytes()
        if sha256(body) != ABOUT_PIN:
            raise ValueError('Approved About copy digest mismatch')
    except (OSError, ValueError):
        return '<main class="about"><h1>About the Research</h1><p>The local About preview is unavailable.</p></main>'
    parts = []
    for paragraph in body.decode().strip().split('\n\n'):
        if paragraph.startswith('**Email:**'):
            parts.append('<div class="contact-controls" aria-label="Email contact"></div>')
        elif paragraph.startswith('# '):
            parts.append('<h1>'+inline(paragraph[2:])+'</h1>')
        elif paragraph.startswith('## '):
            parts.append('<h2>'+inline(paragraph[3:])+'</h2>')
        elif paragraph.startswith(('**GitHub:**','**LinkedIn:**')):
            label, url = paragraph.split(' ', 1)
            parts.append(f'<p>{inline(label)} <a href="{escape(url,quote=True)}" target="_blank" rel="noopener noreferrer">{escape(url)}</a></p>')
        else:
            parts.append('<p>'+inline(paragraph)+'</p>')
    return '<main class="about">'+''.join(parts)+'</main>'


def research_markup():
    references = ''.join(f'<p><a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(title)}</a><br>{escape(claim)}</p>' for title,url,claim in REFERENCES)
    return '<main class="about research-foundation"><h1>Research Foundation</h1>'+references+'</main>'


def render_shell(view):
    # Register in the active Streamlit runtime, including isolated AppTest runtimes.
    # Re-registering the identical definition is supported and does not replace content.
    dashboard = st.components.v2.component(
        'local_evidence_review', html='<div class="review-root"></div>',
        css=(HERE/'review.css').read_text(), js=(HERE/'review.js').read_text(), isolate_styles=True,
    )
    cases=[]
    error=None
    if view == 'Demonstration':
        try:
            catalog=load_catalog()
            cases=[browser_case(c) for c in catalog.cases]
        except (OSError,ValueError) as exc:
            error=exc
    def hide_contact(notice=False):
        st.session_state['contact_revealed'] = False
        st.session_state['contact_hidden_notice'] = notice
    def reveal_contact():
        if view == 'About':
            st.session_state['contact_revealed'] = True
    if view != 'About':
        hide_contact()
    result=dashboard(key='review_shell', data={
        'view':view, 'cases':cases,
        'about':about_markup() if view == 'About' else '',
        'research':research_markup() if view == 'Research' else '',
        'contact':dict(contact_payload(st.session_state.get('contact_revealed', False)),
                       just_hidden=st.session_state.pop('contact_hidden_notice', False)) if view == 'About' else {},
    }, on_navigate_change=hide_contact, on_reveal_contact_change=reveal_contact,
       on_hide_contact_change=lambda:hide_contact(True))
    if result.navigate in VIEWS and result.navigate != view:
        hide_contact()
        st.session_state['review_view']=result.navigate
        st.rerun()
    if error and not isinstance(error, FileNotFoundError):
        st.error('Private preview validation failed. No source excerpts are displayed.')
        with st.expander('Local validation diagnostic'):
            st.text(str(error))
