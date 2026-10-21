"""v0.3.1 private display records. Historical preview and research contracts stay intact."""
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, model_validator

from context_safety.demonstration.preview import (
    Digest, Excerpt, Preview, PreviewCase, Span, Strict, Text,
)
from context_safety.storage.json_io import strict_loads
from context_safety.storage.provenance import sha256

VERSION = 'private-preview-0.3.1'
PROPOSAL_PINS = {
    'CASE-01': '7a81040b3dbabb65a1374bd893d844fc29742520a57b2644f5cc2e8049d1b7e2',
    'CASE-02': '4ac8ba8731a8ff3cdd444e6400b0c7eee9727feb5012de5925547b54a415518e',
    'CASE-03': '8b0615570f322528db5d9d61cda7e1a3222009cf6bd2591c77139ded65df69cc',
}
FullText = Annotated[str, Field(min_length=1)]


class Redaction(Strict):
    start: Annotated[int, Field(ge=0)]
    end: Annotated[int, Field(gt=0)]
    original_sha256: Digest
    replacement: FullText
    reason: Text

    @model_validator(mode='after')
    def explicit_omission(self):
        if self.end <= self.start:
            raise ValueError('Redaction range must be nonempty')
        if not any(marker in self.replacement.lower() for marker in ('[redacted', '[omitted', '[technical correction omitted')):
            raise ValueError('Every withheld span needs a visible omission marker')
        return self


class FullSpan(Span):
    text: FullText


class DisplayRecord(Excerpt):
    text: FullText
    spans: Annotated[list[FullSpan], Field(min_length=1, max_length=1)]
    original_length: Annotated[int, Field(gt=0)]
    redactions: list[Redaction]
    start_expanded: bool

    @model_validator(mode='after')
    def full_record(self):
        span = self.spans[0]
        if span.start_char != 0 or span.end_char != self.original_length:
            raise ValueError('The audited source span must cover the complete message')
        end = 0
        for edit in self.redactions:
            if edit.start < end or edit.end > self.original_length:
                raise ValueError('Overlapping or out-of-range source redactions')
            end = edit.end
            if edit.replacement not in self.text:
                raise ValueError('Redaction marker missing from display record')
        if self.kind == 'verbatim':
            if self.redactions or span.replacement is not None or sha256(self.text.encode()) != span.sha256:
                raise ValueError('Verbatim records must retain the complete original bytes')
        elif not self.redactions or span.replacement != self.text:
            raise ValueError('Redacted/summary records require complete explicit edit provenance')
        return self


class ReviewCase(PreviewCase):
    messages: Annotated[list[DisplayRecord], Field(min_length=1)]
    shared_background: Text
    history_note: str

    @model_validator(mode='after')
    def locked_response(self):
        if sha256(self.proposed.encode()) != PROPOSAL_PINS[self.id]:
            raise ValueError('Approved response differs from the owner-pinned bytes')
        return self


class ReviewPreview(Preview):
    version: Literal['private-preview-0.3.1']
    cases: Annotated[list[ReviewCase], Field(min_length=3, max_length=3)]


def load_review_preview(path: Path) -> ReviewPreview:
    data = path.read_bytes()
    manifest = strict_loads(path.with_name('preview.manifest.json').read_bytes())
    if manifest != {'artifact': path.name, 'version': VERSION, 'sha256': sha256(data)}:
        raise ValueError('Private preview digest mismatch')
    return ReviewPreview.model_validate(strict_loads(data))
