"""Narrow, pinned private display correction over the preserved v0.4.0 contract."""
from pathlib import Path
from typing import Literal

from context_safety.demonstration.outcome_analysis import OutcomePreview, load_outcome_preview
from context_safety.storage.json_io import strict_loads
from context_safety.storage.provenance import sha256

VERSION = 'private-preview-0.4.1'
EDITORIAL_PIN = '3b729ac6ccbc42f7900dd8f07470f743fe52d7d6dbf8a1e1738809f8ef047e6f'
APPROVED_RELEASE_PIN = 'ac89e0da1c64d15f677bf52da5fd9af5e6b2da997b613f0d2434981cf9aae5db'


class PolishPreview(OutcomePreview):
    version: Literal['private-preview-0.4.1']


def load_approved_release(path: Path):
    """Load only the exact owner-approved display bytes, without private archives.

    Publication authorization applies to this digest, not to arbitrary input or
    to the historical publication-status fields preserved inside the fixture.
    The original full source-verification loader below remains unchanged.
    """
    body = path.read_bytes()
    if sha256(body) != APPROVED_RELEASE_PIN:
        raise ValueError('Approved release fixture digest mismatch')
    preview = PolishPreview.model_validate(strict_loads(body))
    from context_safety.ui.evidence import verify_rendered_coverage
    from context_safety.ui.outcome_markup import outcome_case_markup
    for case in preview.cases:
        verify_rendered_coverage(case, outcome_case_markup(case))
    return preview


def approved_revision(previous, editorial_path: Path):
    body = editorial_path.read_bytes()
    if sha256(body) != EDITORIAL_PIN:
        raise ValueError('Approved editorial correction digest mismatch')
    edit = strict_loads(body)
    data = previous.model_dump(mode='json')
    data['version'] = VERSION
    message = next(m for m in data['cases'][2]['messages'] if m['id'] == 'c3-reuse')
    if not message['text'].startswith(edit['old']):
        raise ValueError('Approved correction does not match the historical summary')
    message['text'] = message['text'].replace(edit['old'], edit['new'], 1)
    message['spans'][0]['text'] = message['spans'][0]['replacement'] = message['text']
    message['redactions'][0]['replacement'] = message['text']
    anchor = next(a for n in data['cases'][2]['analysis']['annotations'] for a in n['anchors']
                  if a['id'] == 'c3-followup-reuse-p1')
    anchor.update(display_text=edit['new'], display_end=len(edit['new']),
                  display_span_sha256=sha256(edit['new'].encode()))
    return data


def load_polish_preview(path: Path, baseline_path: Path, source_path: Path):
    body = path.read_bytes()
    manifest = strict_loads(path.with_name('preview.manifest.json').read_bytes())
    if manifest != dict(artifact=path.name, version=VERSION, sha256=sha256(body)):
        raise ValueError('Private polish preview digest mismatch')
    # Replay all historical source verification before permitting the one approved delta.
    previous = load_outcome_preview(path.parent.parent/'v0.4.0-owner-review/preview.json',
                                    baseline_path, source_path)
    expected = approved_revision(previous, path.with_name('editorial.json'))
    data = strict_loads(body)
    if data != expected:
        raise ValueError('Unapproved change to historical preview or analysis')
    return PolishPreview.model_validate(data)
