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


def digest(value):
    return sha256(value).hexdigest()


def test_identical_original_content_and_rendering():
    preview = review_app.load_catalog()
    assert digest(json.dumps(preview.model_dump(mode='json'), sort_keys=True).encode()) == EXPECTED['schema_dump']
    assert digest(json.dumps([browser_case(c) for c in preview.cases], sort_keys=True).encode()) == EXPECTED['browser_cases']
    assert digest(review_app.about_markup().encode()) == EXPECTED['about_html']
    assert digest(review_app.research_markup().encode()) == EXPECTED['research_html']
    assert digest(review_app.ABOUT.read_bytes()) == review_app.ABOUT_PIN


@pytest.mark.parametrize('name', EXPECTED['unchanged_files'])
def test_original_ui_and_contract_bytes(name):
    assert digest((ROOT / name).read_bytes()) == EXPECTED['unchanged_files'][name]


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
