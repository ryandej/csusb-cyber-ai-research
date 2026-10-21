"""Strict local-review contract. Source excerpts are never bundled public assets."""
from pathlib import Path
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from context_safety.storage.json_io import strict_loads
from context_safety.storage.provenance import sha256

Text = Annotated[str, Field(min_length=1, max_length=15000)]
ID = Annotated[str, Field(pattern=r'^[a-z][a-z0-9-]{0,63}$')]
Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True, revalidate_instances='always')


class Span(Strict):
    start_line: Annotated[int, Field(ge=1)]
    end_line: Annotated[int, Field(ge=1)]
    start_char: Annotated[int, Field(ge=0)]
    end_char: Annotated[int, Field(ge=1)]
    sha256: Digest
    replacement: str | None
    text: Text

    @model_validator(mode='after')
    def bounds(self):
        if self.end_line < self.start_line or self.end_char <= self.start_char:
            raise ValueError('Invalid original source span')
        if self.replacement is not None and self.text != self.replacement:
            raise ValueError('Redaction text must be explicit')
        return self


class Excerpt(Strict):
    id: ID
    conversation: Annotated[int, Field(ge=1)]
    turn: Annotated[int, Field(ge=1)]
    role: Literal['User', 'Assistant', 'Platform']
    stage: Text
    group: Literal['main', 'earlier', 'followup']
    critical: bool
    kind: Literal['verbatim', 'redacted', 'summary']
    text: Text
    spans: Annotated[list[Span], Field(min_length=1)]
    request_reference: Text
    omission_note: Text
    summary_note: str

    @model_validator(mode='after')
    def representation(self):
        if self.kind == 'summary' and not self.summary_note:
            raise ValueError('Researcher summaries must be labeled')
        if self.role == 'Platform' and (self.conversation, self.turn) != (8, 2):
            raise ValueError('Only the audited platform outcome belongs in this preview')
        if (self.conversation, self.turn) == (8, 2) and self.role == 'Assistant':
            raise ValueError('A platform error cannot become an assistant answer')
        if self.kind == 'verbatim' and any(s.replacement for s in self.spans):
            raise ValueError('A redaction cannot be called verbatim')
        return self


class Finding(Strict):
    id: ID
    label: Text
    text: Text
    supports: Annotated[list[ID], Field(min_length=1)]
    tone: Literal['context', 'help', 'risk']


class ProposalSource(Strict):
    file: Text
    start_line: int
    end_line: int
    sha256: Digest


class PreviewCase(Strict):
    id: Literal['CASE-01', 'CASE-02', 'CASE-03']
    title: Text
    subtitle: Text
    background: Text
    focus: Text
    branch: Text
    messages: Annotated[list[Excerpt], Field(min_length=1)]
    annotations: Annotated[list[Finding], Field(min_length=1)]
    observed: Text
    assessment: Text
    preferred: Text
    training: Text
    source_qualification: Text
    proposed: Text
    proposal_source: ProposalSource

    @model_validator(mode='after')
    def links_and_branch(self):
        ids = [m.id for m in self.messages]
        if len(ids) != len(set(ids)) or len({a.id for a in self.annotations}) != len(self.annotations):
            raise ValueError('Duplicate preview IDs')
        for a in self.annotations:
            if len(set(a.supports)) != len(a.supports) or not set(a.supports) <= set(ids):
                raise ValueError('Finding must link only to messages in this case')
        for m in self.messages:
            c, t = m.conversation, m.turn
            allowed = ((c == 4 and t < 120) or (c == 7 and t == 1) or (c == 8 and t <= 2)) if self.id == 'CASE-01' else (
                c == 4 and t in (48, 83, 84) if self.id == 'CASE-02' else
                ((c == 4 and t < 16) or (c == 20 and t == 1) or (c == 27 and 2 <= t <= 6)))
            if not allowed:
                raise ValueError('Excerpt crosses the audited branch boundary')
        if sha256(self.proposed.encode()) != self.proposal_source.sha256:
            raise ValueError('Locked proposed response digest mismatch')
        return self


class Preview(Strict):
    version: Literal['private-preview-0.3.0']
    private_only: Literal[True]
    source_publication: Literal['pending_owner_decision']
    research_eligible: Literal[False]
    training_eligible: Literal[False]
    source_sha256: Digest
    cases: Annotated[list[PreviewCase], Field(min_length=3, max_length=3)]

    @model_validator(mode='after')
    def ordering(self):
        if [c.id for c in self.cases] != ['CASE-01', 'CASE-02', 'CASE-03']:
            raise ValueError('Exactly the approved case order is required')
        return self


def load_preview(path: Path) -> Preview:
    data = path.read_bytes()
    manifest = strict_loads(path.with_name('preview.manifest.json').read_bytes())
    if manifest != {'artifact':path.name, 'version':'private-preview-0.3.0', 'sha256':sha256(data)}:
        raise ValueError('Private preview digest mismatch')
    return Preview.model_validate(strict_loads(data))
