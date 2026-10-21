"""Public routing is separate from the explicitly launched local evaluator."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
import pytest
from context_safety.ui import review_app
from context_safety.ui.review_app import about_markup, research_markup
from context_safety.demonstration.research import REFERENCES

ROOT = Path(__file__).resolve().parents[1]


def test_new_landing_has_no_old_primary_controls(monkeypatch):
    for key in ('OPENAI_API_KEY','GROQ_API_KEY','ANTHROPIC_API_KEY','HF_TOKEN'):
        monkeypatch.delenv(key, raising=False)
    app = AppTest.from_file(str(ROOT/'app.py')).run(timeout=20)
    assert not app.exception and not app.error
    assert not app.toggle and not app.radio and not app.selectbox
    assert len(app.get('bidi_component')) == 1
    assert not app.title and not app.get('download_button')


def test_research_is_reading_list_and_never_calls_evaluator(monkeypatch):
    import importlib.util
    assert importlib.util.find_spec('context_safety.ui.advanced') is None
    for view in ('Research','About','Demonstration','advanced','developer','Research?tools=true'):
        app = AppTest.from_file(str(ROOT/'app.py'))
        app.session_state['review_view'] = view
        app.session_state['advanced'] = True
        app.run(timeout=20)
        assert not app.exception
        assert not app.selectbox and not app.file_uploader and not app.get('download_button')
    html = research_markup()
    assert '<h1>Research Foundation</h1>' in html
    assert html.count('<a ') == 7
    for title, url, claim in REFERENCES:
        assert f'href="{url}"' in html


def test_about_uses_approved_heading_and_keeps_references_on_research():
    about = about_markup()
    assert '<h1>Overview</h1>' in about
    assert [part.split('</h2>')[0] for part in about.split('<h2>')[1:]] == ['Demonstration', 'Author', 'Contact']
    assert '<strong>' not in about.split('<h2>Contact</h2>')[0]
    assert 'https://github.com/ryandej' in about
    assert 'Research Foundation' not in about
    assert all(url not in about for _,url,_ in REFERENCES)
    assert 'sponsorship' not in about and 'publication permission' not in about
    app = AppTest.from_file(str(ROOT/'app.py'))
    app.session_state['review_view'] = 'About'
    app.run(timeout=20)
    assert not app.exception and not app.selectbox


@pytest.mark.parametrize('corrupt', [False, True])
def test_missing_or_invalid_private_fixture_keeps_research_available(monkeypatch,tmp_path,corrupt):
    path = tmp_path/'preview.json'
    if corrupt:
        path.write_text('{}')
        path.with_name('preview.manifest.json').write_text('{}')
    monkeypatch.setattr(review_app,'PREVIEW',path)
    app = AppTest.from_file(str(ROOT/'app.py')).run(timeout=20)
    assert not app.exception
    assert bool(app.error) == corrupt
    assert not app.selectbox and not app.get('download_button')
    app.session_state['review_view'] = 'Research'
    app.run()
    assert not app.exception and not app.error and not app.selectbox
