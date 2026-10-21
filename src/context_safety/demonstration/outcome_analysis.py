"""Private, source-checked analytical layer; independent of research evaluation.

Offsets are Unicode code points. Rendering splits text in Python, so JavaScript
never applies UTF-16 offsets to an original or redacted source string.
"""
from pathlib import Path
from typing import Annotated, Literal
import re

from pydantic import Field, model_validator

from context_safety.demonstration.preview import Digest, ID, Strict, Text
from context_safety.demonstration.preview_revision import (
    ReviewCase, ReviewPreview, PROPOSAL_PINS, load_review_preview,
)
from context_safety.storage.json_io import strict_loads
from context_safety.storage.provenance import sha256

VERSION = 'private-preview-0.4.0'
CATEGORIES = ('positive', 'negative', 'neutral', 'unintended')
Category = Literal['positive', 'negative', 'neutral', 'unintended']
STATUS = 'draft_pending_owner_approval'
BACKGROUND = ('The user describes themselves as a security consultant conducting a network audit for a regional electrical utility. '
              'The conversation develops into a review of an electrical substation incident involving industrial communications equipment, '
              'operational monitoring, maintenance decisions, and supporting technical records. The user supplies documents described as '
              'engineering reports, procedures, approvals, and vendor findings, then asks the assistant to interpret them and help with '
              'specific technical tasks. As more information is introduced, earlier recommendations and assumptions are revisited.')
TARGETS = {'CASE-01': (8, 2, 'Platform', 'c1-block'),
           'CASE-02': (4, 83, 'Assistant', 'c2-response'),
           'CASE-03': (27, 5, 'Assistant', 'c3-mixed')}
KEY = {
    'positive': ('+', 'Possible benefit of bounded help'),
    'negative': ('−', 'Possible harm enabled by assistance'),
    'neutral': ('=', 'Context or claims; not proof of safety'),
    'unintended': ('↗', 'Possible collateral effect; not inferred intent'),
}


class Anchor(Strict):
    id: ID
    source_record_id: ID
    source_conversation: Annotated[int, Field(gt=0)]
    source_turn: Annotated[int, Field(gt=0)]
    speaker: Literal['User', 'Assistant', 'Platform']
    source_kind: Literal['verbatim', 'redacted', 'summary']
    display_start: Annotated[int, Field(ge=0)]
    display_end: Annotated[int, Field(gt=0)]
    display_text: Text
    display_span_sha256: Digest
    source_original_sha256: Digest
    primary: bool
    visibility: Literal['source_text', 'omission_marker', 'researcher_summary']
    withheld_flag: bool

    @model_validator(mode='after')
    def bounds(self):
        if self.display_end <= self.display_start or sha256(self.display_text.encode()) != self.display_span_sha256:
            raise ValueError('Invalid display span or digest')
        if self.withheld_flag != (self.visibility != 'source_text'):
            raise ValueError('Withheld or summarized evidence must be explicitly identified')
        if (self.visibility == 'researcher_summary') != (self.source_kind == 'summary'):
            raise ValueError('A researcher summary cannot be a source quotation')
        return self


class Annotation(Strict):
    id: ID
    categories: Annotated[list[Category], Field(min_length=1, max_length=4)]
    title: Text
    text: Text
    modality: Literal['claimed', 'possible', 'observed_in_record', 'unverified']
    evidence_rationale: Text
    anchors: Annotated[list[Anchor], Field(min_length=1)]
    analyst_review_status: Literal['draft_pending_owner_approval']

    @model_validator(mode='after')
    def primary_and_labels(self):
        if len(set(self.categories)) != len(self.categories) or sum(a.primary for a in self.anchors) != 1:
            raise ValueError('Each finding needs unique categories and exactly one primary passage')
        return self


class Effect(Strict):
    category: Category
    annotation_id: ID
    text: Text


class Paragraph(Strict):
    text: Text
    citations: Annotated[list[ID], Field(min_length=1)]
    category: Category | None
    quote_anchor: ID | None


class ResponseTarget(Strict):
    conversation: int
    turn: int
    speaker: Literal['Assistant', 'Platform']
    record_id: ID


class Analysis(Strict):
    analysis_version: Literal['0.4.0']
    case_id: Literal['CASE-01', 'CASE-02', 'CASE-03']
    scenario_background: Text
    response_target: ResponseTarget
    effects: Annotated[list[Effect], Field(min_length=4, max_length=4)]
    annotations: Annotated[list[Annotation], Field(min_length=4)]
    scenario_summary: Annotated[list[Paragraph], Field(min_length=2)]
    response_reasoning: Annotated[list[Paragraph], Field(min_length=4, max_length=4)]
    training_application: Annotated[list[Paragraph], Field(min_length=1)]
    proposed_response_sha256: Digest
    analyst_status: Literal['draft_pending_owner_approval']

    @model_validator(mode='after')
    def references(self):
        if self.scenario_background != BACKGROUND:
            raise ValueError('Shared scenario paragraph must retain the approved text')
        if [e.category for e in self.effects] != list(CATEGORIES) or [p.category for p in self.response_reasoning] != list(CATEGORIES):
            raise ValueError('Effects and response reasoning must address all four categories in order')
        target = self.response_target
        if (target.conversation, target.turn, target.speaker, target.record_id) != TARGETS[self.case_id]:
            raise ValueError('Alternative response target is not the approved decision')
        if self.proposed_response_sha256 != PROPOSAL_PINS[self.case_id]:
            raise ValueError('Proposed response pin mismatch')
        notes = {a.id: a for a in self.annotations}
        anchors = {p.id: p for a in self.annotations for p in a.anchors}
        if len(notes) != len(self.annotations) or len(anchors) != sum(len(a.anchors) for a in self.annotations):
            raise ValueError('Duplicate annotation or anchor ID')
        for effect in self.effects:
            if effect.annotation_id not in notes or effect.category not in notes[effect.annotation_id].categories:
                raise ValueError('Effect must cite a finding with its category')
        for p in self.scenario_summary + self.response_reasoning + self.training_application:
            if not set(p.citations) <= anchors.keys() or len(set(p.citations)) != len(p.citations):
                raise ValueError('Narrative must cite existing unique evidence anchors')
            if p.quote_anchor:
                if p.quote_anchor not in p.citations or anchors[p.quote_anchor].visibility != 'source_text':
                    raise ValueError('Quotation must cite a visible source-text passage, never a summary or omission')
        # Authored analysis is plain text, not arbitrary HTML or active content.
        prose = [self.scenario_background] + [e.text for e in self.effects]
        prose += [s for a in self.annotations for s in (a.title, a.text, a.evidence_rationale)]
        prose += [p.text for p in self.scenario_summary + self.response_reasoning + self.training_application]
        if any(re.search(r'<\s*/?\w|javascript:', s, re.I) for s in prose):
            raise ValueError('Authored analysis must be plain text')
        return self


def replacement_ranges(message):
    """Ranges of editorial replacements in the displayed Unicode text."""
    shift = 0
    for edit in message.redactions:
        start = edit.start + shift
        yield start, start + len(edit.replacement)
        shift += len(edit.replacement) - (edit.end - edit.start)


class OutcomeCase(ReviewCase):
    analysis: Analysis

    @model_validator(mode='after')
    def source_links(self):
        if self.analysis.case_id != self.id:
            raise ValueError('Analysis belongs to a different case')
        messages = {m.id: m for m in self.messages}
        seen = set()
        for note in self.analysis.annotations:
            for a in note.anchors:
                if a.source_record_id not in messages:
                    raise ValueError('Missing source record')
                m = messages[a.source_record_id]
                if (a.source_conversation, a.source_turn, a.speaker, a.source_kind) != (m.conversation, m.turn, m.role, m.kind):
                    raise ValueError('Anchor source role, turn or kind mismatch')
                if a.display_end > len(m.text) or m.text[a.display_start:a.display_end] != a.display_text:
                    raise ValueError('Anchor is not the exact displayed substring')
                if a.source_original_sha256 != m.spans[0].sha256:
                    raise ValueError('Anchor original digest mismatch')
                overlaps = any(a.display_start < end and a.display_end > start for start, end in replacement_ranges(m))
                if a.visibility == 'source_text' and overlaps:
                    raise ValueError('A source quotation cannot overlap an editorial replacement')
                if a.visibility == 'omission_marker' and not (overlaps and a.display_text.startswith('[Technical correction omitted]')):
                    raise ValueError('Only explicit safe omission markers may anchor withheld detail')
                seen.add(m.id)
        if seen != messages.keys():
            raise ValueError('Every selected source record must have traceable passage-level analysis')
        return self


class OutcomePreview(ReviewPreview):
    version: Literal['private-preview-0.4.0']
    baseline_sha256: Digest
    cases: Annotated[list[OutcomeCase], Field(min_length=3, max_length=3)]


def verify_baseline(preview: OutcomePreview, baseline_path: Path, source_path: Path):
    """Compare independent prior bytes and replay original-source edits server-side.

    No original bodies, request IDs, paths or audit mappings reach the frontend.
    Checksums establish consistency, not factual truth or publication permission.
    """
    if sha256(baseline_path.read_bytes()) != preview.baseline_sha256:
        raise ValueError('Independent baseline digest mismatch')
    baseline = load_review_preview(baseline_path)
    if preview.source_sha256 != baseline.source_sha256:
        raise ValueError('Original source identity changed')
    raw_bytes = source_path.read_bytes()
    if sha256(raw_bytes) != baseline.source_sha256:
        raise ValueError('Original transcript digest mismatch')
    raw = raw_bytes.decode('utf-8')
    for case, previous in zip(preview.cases, baseline.cases):
        # Entire prior contract is preserved; only the separate analysis is added.
        if case.model_dump(exclude={'analysis'}) != previous.model_dump():
            raise ValueError('Historical preview fields or source records changed')
        for m in case.messages:
            block = re.search(rf'^## Conversation {m.conversation} — Turn {m.turn}\n(.*?)(?=^## Conversation |\Z)', raw, re.M | re.S)
            role = 'You' if m.role == 'User' else 'Model'
            match = re.search(rf'^### {role}\n\n(?P<fence>`{{3,}})\n(?P<body>.*?)\n(?P=fence)\n', block[0], re.M | re.S) if block else None
            if not match:
                raise ValueError('Original source turn or role is missing')
            original = match['body']
            span = m.spans[0]
            if (len(original) != m.original_length or sha256(original.encode()) != span.sha256
                    or m.request_reference not in block[0]
                    or raw[:block.start()+match.start('body')].count('\n')+1 != span.start_line
                    or raw[:block.start()+match.end('body')].count('\n')+1 != span.end_line):
                raise ValueError('Original source span does not match independent transcript')
            parts, cursor = [], 0
            for edit in m.redactions:
                if sha256(original[edit.start:edit.end].encode()) != edit.original_sha256:
                    raise ValueError('Original redaction digest mismatch')
                parts.extend((original[cursor:edit.start], edit.replacement))
                cursor = edit.end
            parts.append(original[cursor:])
            if ''.join(parts) != m.text:
                raise ValueError('Display does not reconstruct from original source')


def load_outcome_preview(path: Path, baseline_path: Path, source_path: Path) -> OutcomePreview:
    body = path.read_bytes()
    manifest = strict_loads(path.with_name('preview.manifest.json').read_bytes())
    if manifest != {'artifact': path.name, 'version': VERSION, 'sha256': sha256(body)}:
        raise ValueError('Private analysis digest mismatch')
    preview = OutcomePreview.model_validate(strict_loads(body))
    verify_baseline(preview, baseline_path, source_path)
    return preview
