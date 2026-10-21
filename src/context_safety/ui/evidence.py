"""Shared display segmentation and exhaustive bidirectional coverage audit."""
import re
from context_safety.demonstration.outcome_analysis import replacement_ranges, CATEGORIES
from context_safety.storage.provenance import sha256


def redaction_markers(message):
    """Only verified omission placeholders, never the surrounding summary prose."""
    result = []
    for index, ((start, _), edit) in enumerate(zip(replacement_ranges(message), message.redactions)):
        matches = list(re.finditer(r'\[(?:redacted|omitted|technical correction omitted)[^\]]*\]', edit.replacement, re.I))
        if len(matches) != 1:
            raise ValueError('Each recorded redaction must have one explicit source-status marker')
        match = matches[0]
        result.append((start+match.start(), start+match.end(), f'{message.id}-redaction-{index+1}'))
    return result


def segments(text, entries, redactions=()):
    points = sorted({0, len(text), *(v for _, a in entries for v in (a.display_start, a.display_end)),
                     *(v for start, end, _ in redactions for v in (start, end))})
    for start, end in zip(points, points[1:]):
        if start < 0 or end > len(text):
            raise ValueError('Invalid display offsets')
        active = [(n,a) for n,a in entries if a.display_start <= start and a.display_end >= end]
        status = next((id for a,b,id in redactions if a <= start and b >= end), None)
        yield start, end, active, status


def coverage_audit(cases):
    spans, descriptions, redactions = [], [], []
    for case in cases:
        for message in case.messages:
            entries = [(n,a) for n in case.analysis.annotations for a in n.anchors if a.source_record_id==message.id]
            markers = redaction_markers(message)
            for start,end,active,status in segments(message.text,entries,markers):
                if not active and not status:
                    continue
                ids = [f'finding-{n.id}-{cat}' for n,_ in active for cat in n.categories]
                item = dict(id=f'{message.id}-span-{start}-{end}',case_id=case.id,source_id=message.id,
                            conversation=message.conversation,turn=message.turn,display_start=start,display_end=end,
                            display_text_sha256=sha256(message.text[start:end].encode()),
                            anchor_ids=[a.id for _,a in active],
                            categories=[] if status else list(dict.fromkeys(c for n,_ in active for c in n.categories)),
                            description_ids=ids,explanations=[n.text for n,_ in active],
                            anchors=[a.model_dump() for _,a in active],
                            click_test_id='H02/'+case.id+'/'+str(start),status='withheld' if status else 'semantic')
                if status:
                    item['redaction_id']=status;redactions.append(item)
                else:
                    if not ids or any(not n.text.strip() for n,_ in active):
                        raise ValueError('Orphan semantic highlight')
                    spans.append(item)
        for n in case.analysis.annotations:
            for cat in n.categories:
                id=f'finding-{n.id}-{cat}'
                targets=[s['id'] for s in spans+redactions if id in s['description_ids']]
                if not targets:
                    raise ValueError('Description has no displayed or explicitly withheld target')
                descriptions.append(dict(id=id,case_id=case.id,annotation_id=n.id,category=cat,
                                         explanation=n.text,rationale=n.evidence_rationale,targets=targets,click_test_id='H03/'+id))
    return dict(spans=spans,descriptions=descriptions,redactions=redactions,
                counts=dict(semantic_spans=len(spans),description_entries=len(descriptions),redacted_markers=len(redactions),
                            historical_anchors=sum(len(n.anchors) for c in cases for n in c.analysis.annotations),
                            orphans=0,invalid_offsets=0))


def verify_rendered_coverage(case, rendered):
    """Independently check actual HTML IDs/links, including lazy source templates."""
    from html.parser import HTMLParser
    class Nodes(HTMLParser):
        def __init__(self):
            super().__init__(); self.passages=[]; self.ids=set(); self.targets=set()
        def handle_starttag(self, tag, attrs):
            a=dict(attrs)
            if 'id' in a: self.ids.add(a['id'])
            if 'data-anchor' in a: self.targets.add(a['data-anchor'])
            if 'passage' in a.get('class','').split(): self.passages.append(a)
    nodes=Nodes(); nodes.feed(rendered)
    expected=coverage_audit([case]); spans={s['id']:s for s in expected['spans']}
    if {a.get('data-passage') for a in nodes.passages} != spans.keys() or len(nodes.passages)!=len(spans):
        raise ValueError('Rendered semantic highlight coverage mismatch')
    for node in nodes.passages:
        item=spans[node['data-passage']]
        if (set(node.get('data-anchors','').split())!=set(item['anchor_ids'])
                or set(node.get('data-categories','').split())!=set(item['categories'])
                or not set(item['description_ids'])<=nodes.ids or node.get('tabindex')!='0' or node.get('role')!='button'):
            raise ValueError('Orphan or inaccessible rendered semantic highlight')
    for note in case.analysis.annotations:
        if not {a.id for a in note.anchors}<=nodes.targets:
            raise ValueError('Missing inverse evidence pointer')
    expected['counts']['inaccessible_items']=0
    return expected
