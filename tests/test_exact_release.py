"""Exact approved content, original rendering, and fail-closed release loading."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

from context_safety.demonstration import polish_preview
from context_safety.ui import review_app
from context_safety.ui.outcome_markup import browser_case

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = json.loads((ROOT / 'tests/original-render-fingerprints.json').read_text())
PRESENTATION_SUBSTITUTIONS = {
    'app.py': [(b"page_title='Context-Aware AI Safety'",
                b"page_title='Context-Aware LLM Safety Classifier'")],
    'src/context_safety/ui/review.js': [
        (b'<h1>Context-Aware AI Safety</h1>', b'<h1>Context-Aware LLM Safety Classifier</h1>'),
        (b'<p>Cybersecurity assistance, risk, and utility</p>',
         b'<p>Reducing unnecessary refusals while maintaining safeguards against harmful assistance.</p>'),
    ],
    'src/context_safety/ui/review_app.py': [
        (b"ABOUT_PIN = '891b20f6aa78bf6f75831e8b48ef6bbdb7bffa564caab4f8e638df00159c9976'",
         b"ABOUT_PIN = '14e4cd9a456fc5efb3a258284b5a12d4470d45a22116924d4901de3d5669bbe1'"),
        (b"ABOUT = DISPLAY / 'about.md'", b"ABOUT = ROOT / 'data/presentation/2026-10-21/about.md'"),
    ],
}
PROTECTED_FILES = dict(EXPECTED['unchanged_files'], **{
    'src/context_safety/ui/review_app.py': 'cf5b840dc0e3e4ff3370c0b0fb7ac496110dfd78c32cfa3db158fbd40ce41fdb',
})
HISTORICAL_ABOUT_PIN = '891b20f6aa78bf6f75831e8b48ef6bbdb7bffa564caab4f8e638df00159c9976'
CURRENT_ABOUT_PIN = '14e4cd9a456fc5efb3a258284b5a12d4470d45a22116924d4901de3d5669bbe1'
CURRENT_ABOUT_HTML_PIN = '0d43ed9e5cf083f5f23e3ab474f21d8fca3569e60a30e82ebfff2b0773b5c0fe'


def original_bytes_after_approved_presentation(name, body):
    """Reverse only exact owner-authorized header and About path/pin changes."""
    for old, new in PRESENTATION_SUBSTITUTIONS.get(name, []):
        assert body.count(new) == 1, 'Missing or duplicated approved literal'
        assert old not in body, 'Old literal remains'
        body = body.replace(new, old, 1)
    return body


def digest(value):
    return sha256(value).hexdigest()


def test_identical_original_content_and_rendering():
    preview = review_app.load_catalog()
    assert digest(json.dumps(preview.model_dump(mode='json'), sort_keys=True).encode()) == EXPECTED['schema_dump']
    assert digest(json.dumps([browser_case(c) for c in preview.cases], sort_keys=True).encode()) == EXPECTED['browser_cases']
    assert digest(review_app.research_markup().encode()) == EXPECTED['research_html']


@pytest.mark.parametrize('name', PROTECTED_FILES)
def test_original_ui_and_contract_bytes(name):
    body = original_bytes_after_approved_presentation(name, (ROOT / name).read_bytes())
    assert digest(body) == PROTECTED_FILES[name]


@pytest.mark.parametrize('name', PRESENTATION_SUBSTITUTIONS)
@pytest.mark.parametrize('attack', ['extra_code', 'changed_spacing', 'duplicate_literal', 'old_literal', 'wrong_literal'])
def test_presentation_allowance_rejects_other_file_changes(name, attack):
    body = (ROOT / name).read_bytes()
    old, new = PRESENTATION_SUBSTITUTIONS[name][0]
    if attack == 'extra_code':
        body += b'\nunauthorized_change()\n'
    elif attack == 'changed_spacing':
        body = b' ' + body
    elif attack == 'duplicate_literal':
        body += new
    elif attack == 'old_literal':
        body = body.replace(new, old, 1)
    else:
        body = body.replace(new, new[:-1] + b'UNAPPROVED' + new[-1:], 1)
    with pytest.raises(AssertionError):
        normalized = original_bytes_after_approved_presentation(name, body)
        assert digest(normalized) == PROTECTED_FILES[name]


def test_current_and_historical_about_integrity_and_unchanged_contact(monkeypatch):
    historical = ROOT / 'data/approved/v0.4.1/about.md'
    assert digest(historical.read_bytes()) == HISTORICAL_ABOUT_PIN
    assert review_app.ABOUT == ROOT / 'data/presentation/2026-10-21/about.md'
    assert digest(review_app.ABOUT.read_bytes()) == review_app.ABOUT_PIN == CURRENT_ABOUT_PIN
    current_html = review_app.about_markup()
    assert digest(current_html.encode()) == CURRENT_ABOUT_HTML_PIN
    assert review_app.ABOUT.read_bytes().split(b'## Contact\n', 1)[1] == historical.read_bytes().split(b'## Contact\n', 1)[1]
    with monkeypatch.context() as m:
        m.setattr(review_app, 'ABOUT', historical)
        m.setattr(review_app, 'ABOUT_PIN', HISTORICAL_ABOUT_PIN)
        original_html = review_app.about_markup()
        assert digest(original_html.encode()) == EXPECTED['about_html']
    assert current_html.split('<h2>Contact</h2>', 1)[1] == original_html.split('<h2>Contact</h2>', 1)[1]


@pytest.mark.parametrize('replacement', ['historical', 'whitespace', 'changed_copy'])
def test_current_about_rejects_old_or_resealed_content(tmp_path, monkeypatch, replacement):
    original = review_app.ABOUT.read_bytes()
    if replacement == 'historical':
        body = (ROOT / 'data/approved/v0.4.1/about.md').read_bytes()
    elif replacement == 'whitespace':
        body = original + b'\n'
    else:
        body = original.replace(b'# Overview', b'# Replacement', 1)
    path = tmp_path / 'about.md'
    path.write_bytes(body)
    path.with_suffix('.manifest.json').write_text(json.dumps({'sha256': digest(body)}))
    monkeypatch.setattr(review_app, 'ABOUT', path)
    assert 'unavailable' in review_app.about_markup()
    assert 'LOG(N)' not in review_app.about_markup()


def test_packaged_loader_needs_no_private_archives(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Public rendering must not read private source archives')
    monkeypatch.setattr(review_app, 'load_polish_preview', forbidden)
    monkeypatch.setattr(polish_preview, 'load_outcome_preview', forbidden)
    assert review_app.USE_APPROVED_RELEASE
    assert review_app.PREVIEW.is_relative_to(ROOT / 'data/approved')
    assert not review_app.BASELINE.exists() and not review_app.SOURCE.exists()
    assert len(review_app.load_catalog().cases) == 3
    for name, module in list(sys.modules.items()):
        if name.startswith('context_safety') and getattr(module, '__file__', None):
            assert Path(module.__file__).resolve().is_relative_to(ROOT / 'src')


@pytest.mark.parametrize('body', [None, b'{}', b'{"research_eligible":true}', b'[]'])
def test_missing_or_invalid_package_never_falls_back(monkeypatch, tmp_path, body):
    path = tmp_path / 'preview.json'
    if body is not None:
        path.write_bytes(body)
    monkeypatch.setattr(review_app, 'PREVIEW', path)
    monkeypatch.setattr(review_app, 'load_polish_preview', lambda *args: pytest.fail('Unsafe fallback'))
    with pytest.raises((OSError, ValueError)):
        review_app.load_catalog()


@pytest.mark.parametrize('field,value', [
    ('private_only', False), ('source_publication', 'approved'),
    ('research_eligible', True), ('training_eligible', True),
    ('version', 'release-0.4.1'),
])
def test_imported_claims_cannot_authorize_content(tmp_path, field, value):
    data = json.loads(review_app.PREVIEW.read_bytes())
    data[field] = value
    path = tmp_path / 'preview.json'
    path.write_text(json.dumps(data))
    # A freshly authored manifest cannot replace the code-pinned approval.
    path.with_name('preview.manifest.json').write_text(json.dumps({'sha256': digest(path.read_bytes())}))
    with pytest.raises(ValueError, match='digest mismatch'):
        polish_preview.load_approved_release(path)


def test_whitespace_only_mutation_is_rejected(tmp_path):
    path = tmp_path / 'preview.json'
    path.write_bytes(review_app.PREVIEW.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='digest mismatch'):
        polish_preview.load_approved_release(path)


@pytest.mark.parametrize('body', [None, b'# Replacement About'])
def test_about_fails_closed_on_missing_or_changed_copy(tmp_path, monkeypatch, body):
    path = tmp_path / 'about.md'
    if body is not None:
        path.write_bytes(body)
    monkeypatch.setattr(review_app, 'ABOUT', path)
    markup = review_app.about_markup()
    assert 'unavailable' in markup and 'Replacement' not in markup


def test_historical_metadata_is_preserved_not_an_authorization_switch():
    data = review_app.load_catalog()
    assert data.private_only is True
    assert data.source_publication == 'pending_owner_decision'
    assert data.research_eligible is False and data.training_eligible is False


def test_no_developer_or_rejected_entrypoint_in_release():
    for name in ('public_app.py', 'public_demo', 'tests_public', 'scripts/developer_app.py',
                 'src/context_safety/ui/advanced.py', '.streamlit/secrets.toml'):
        assert not (ROOT / name).exists()
