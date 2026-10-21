"""Escaped presentation of the private contextual-outcome layer.

Original text is segmented in Python code-point space. An overlapping passage
uses one mark with explicit labels, never stacked opaque text overlays.
"""
from html import escape

from context_safety.demonstration.outcome_analysis import KEY, CATEGORIES
from context_safety.ui.review_markup import markdown
from context_safety.ui.evidence import segments, redaction_markers


def chip(category, attrs=''):
    symbol = KEY[category][0]
    return f'<button class="outcome-chip {category}" {attrs}><span aria-hidden="true">{symbol}</span> {category.title()}</button>'


def marked_text(text, entries, redactions=(), record='passage'):
    parts = []
    for start, end, active, status in segments(text, entries, redactions):
        value = escape(text[start:end])
        ids = ' '.join(a.id for _, a in active)
        if status:
            attrs = f' data-anchors="{ids}" role="button" tabindex="0"' if active else ''
            parts.append(f'<span class="redacted-status" data-redaction="{status}"{attrs} '
                         f'aria-label="Redacted: deliberate source omission; no outcome classification">{value}</span>')
        elif active:
            categories = list(dict.fromkeys(c for note, _ in active for c in note.categories))
            labels = ', '.join(c.title() for c in categories)
            kind = active[0][1].visibility.replace('_', ' ')
            parts.append(f'<mark class="passage {categories[0]}{" multi-label" if len(categories)>1 else ""}" '
                         f'data-passage="{record}-span-{start}-{end}" data-anchors="{ids}" data-categories="{" ".join(categories)}" '
                         f'role="button" tabindex="0" aria-label="{escape(labels)} evidence; {escape(kind)}; explore explanation">{value}</mark>')
        else:
            parts.append(value)
    return ''.join(parts)


def source_message(message, analysis):
    entries = [(n, a) for n in analysis.annotations for a in n.anchors if a.source_record_id == message.id]
    ref = f'C{message.conversation} T{message.turn}'
    kind = {'verbatim': '', 'redacted': '', 'summary': 'Researcher summary'}[message.kind]
    role = 'Platform block' if message.role == 'Platform' else message.role
    chips, seen = [], set()
    for note, anchor in entries:
        for category in note.categories:
            if category not in seen:
                chips.append(chip(category, f'data-note="{note.id}" data-anchor="{anchor.id}" data-category="{category}" aria-pressed="false"'))
                seen.add(category)
    text = message.text
    prefix = text[:205]
    return f'''<article class="timeline-item {message.role.lower()}{' critical' if message.critical else ''}" id="{message.id}"
        data-message="{message.id}" aria-labelledby="{message.id}-ref {message.id}-speaker" tabindex="-1">
      <div class="timeline-marker"><span class="dot"></span><strong id="{message.id}-ref">{ref}</strong>
        <small>{escape(message.stage)}</small><small class="source-kind">{kind}</small>
        <div class="turn-chips analysis-only">{''.join(chips)}</div></div>
      <div class="speech"><div class="speech-role" id="{message.id}-speaker">{role}<span class="evidence-label" hidden>Selected evidence</span><span class="linked-label" hidden>Linked evidence</span></div>
        <details class="excerpt"{' open' if message.start_expanded else ''}>
          <summary aria-expanded="{'true' if message.start_expanded else 'false'}"><span class="excerpt-preview"><span class="preview-text">{marked_text(prefix, [], [(a,min(b,len(prefix)),id) for a,b,id in redaction_markers(message) if a<len(prefix)], message.id)}</span>{'<span class="ellipsis"> …</span>' if len(text)>205 else ''}</span><span class="expand-label">{'Minimize' if message.start_expanded else 'Expand'}</span></summary>
          <template class="source-template"><div class="full-excerpt">{marked_text(text, entries, redaction_markers(message), message.id)}</div></template><div class="source-body"></div>
        </details></div></article>'''


def anchors_by_id(analysis):
    return {a.id: (note, a) for note in analysis.annotations for a in note.anchors}


def citation(anchor_id, lookup, label=None):
    note, anchor = lookup[anchor_id]
    text = label or f'C{anchor.source_conversation} T{anchor.source_turn} · {anchor.speaker}'
    if anchor.source_kind == 'summary':
        text += ' · researcher summary'
    return f'<button class="source-link" data-note="{note.id}" data-anchor="{anchor.id}" aria-pressed="false">{escape(text)}</button>'


def narrative(title, css, paragraphs, lookup):
    parts = []
    for p in paragraphs:
        heading = f'<h3 class="category-heading {p.category}"><span aria-hidden="true">{KEY[p.category][0]}</span> {p.category.title()}</h3>' if p.category else ''
        quote = ''
        if p.quote_anchor:
            _, a = lookup[p.quote_anchor]
            quote = f'<blockquote>{escape(a.display_text)}<div>{citation(a.id, lookup)}</div></blockquote>'
        links = ' '.join(citation(a, lookup) for a in p.citations)
        parts.append(f'<div class="narrative-paragraph">{heading}<p>{escape(p.text)}</p>{quote}<div class="citations" aria-label="Supporting passages">{links}</div></div>')
    return f'<section class="panel {css} analysis-only" id="{css}"><h2>{title}</h2><div class="narrative-body">{"".join(parts)}</div></section>'


def context_panel(analysis, lookup):
    legend = ''.join(f'<li class="{cat}"><span class="key-symbol" aria-hidden="true">{KEY[cat][0]}</span><span><strong>{cat.title()}</strong>: {KEY[cat][1]}</span></li>' for cat in CATEGORIES)
    groups = []
    for category in CATEGORIES:
        notes = [n for n in analysis.annotations if category in n.categories]
        findings = []
        for note in notes:
            primary = next(a for a in note.anchors if a.primary)
            labels = ' · '.join(c.title() for c in note.categories)
            source_label = {'source_text': 'Source passage', 'omission_marker': 'Specific source detail withheld', 'researcher_summary': 'Researcher summary, not a quotation'}[primary.visibility]
            supporting = ' '.join(citation(a.id, lookup) for a in note.anchors if not a.primary)
            findings.append(f'''<div class="finding-group" id="finding-{note.id}-{category}" data-category="{category}">
              <button class="finding {category}" data-note="{note.id}" data-anchor="{primary.id}" data-category="{category}" aria-pressed="false">
                <span class="finding-title">{escape(note.title)}</span><span class="finding-category">{labels} · {note.modality.replace('_',' ')}</span>
                <span class="finding-text">{escape(note.text)}</span><span class="passage-label">{source_label} · C{primary.source_conversation} T{primary.source_turn} · {primary.speaker}</span>
                <span class="finding-excerpt">{escape(primary.display_text)}</span></button>
              {f'<div class="support-links"><span>Linked evidence</span> {supporting}</div>' if supporting else ''}</div>''')
        empty = '<p class="empty-evidence">No evidence annotated in this category</p>'
        groups.append(f'<details class="evidence-group {category}" data-group="{category}"'+(' open' if category=='positive' else '')+
                      f'><summary><span>{KEY[category][0]} {category.title()}</span><span class="group-count">{len(notes)} '+('entry' if len(notes)==1 else 'entries')+'</span></summary><div class="findings">'+(''.join(findings) or empty)+'</div></details>')
    return f'''<aside class="panel context-panel analysis-only"><h2>Context and evidence</h2>
      <div class="evidence-key"><h3>Key</h3><ul>{legend}</ul>
      <div class="status-key"><span class="redacted-status">Redacted</span> Source detail deliberately omitted.<br>
      <span class="selection-key">Selected evidence</span> Active source turn.</div></div>
      <p class="analysis-attribution">Explore researcher-proposed effects and the passages supporting them. These describe assistance, not user motives.</p>
      <div class="evidence-options" hidden tabindex="-1" role="group" aria-label="Choose an evidence explanation"></div>
      {''.join(groups)}</aside>'''


def outcome_case_markup(case):
    analysis = case.analysis
    lookup = anchors_by_id(analysis)
    timeline, grouped = [], []

    def flush():
        if grouped:
            title = 'Earlier context' if grouped[0].group == 'earlier' else 'Follow-up exchange'
            refs = ', '.join(dict.fromkeys(f'C{m.conversation} T{m.turn}' for m in grouped))
            timeline.append(f'<details class="history-group"><summary>{title} <span>{refs}</span></summary>'+''.join(source_message(m, analysis) for m in grouped)+'</details>')
            grouped.clear()

    for message in case.messages:
        if message.group != 'main':
            if grouped and grouped[-1].group != message.group:
                flush()
            grouped.append(message)
        else:
            flush()
            timeline.append(source_message(message, analysis))
    flush()
    effects = []
    for effect in analysis.effects:
        note = next(n for n in analysis.annotations if n.id == effect.annotation_id)
        anchor = next(a for a in note.anchors if a.primary)
        effects.append(f'<button class="effect-card {effect.category}" data-note="{note.id}" data-anchor="{anchor.id}" data-category="{effect.category}" aria-pressed="false"><strong><span aria-hidden="true">{KEY[effect.category][0]}</span> {effect.category.title()}</strong><span>{escape(effect.text)}</span><small>Explore evidence →</small></button>')
    target = analysis.response_target
    history = f'<p class="history-note">{escape(case.history_note)}</p>' if case.history_note else ''
    return f'''<section class="panel background"><h2>Scenario background</h2><p>{escape(analysis.scenario_background)}</p></section>
      <section class="effects analysis-only"><h2>Potential effects of assistance</h2><div class="effect-grid">{''.join(effects)}</div></section>
      <div class="evidence-grid">
        <section class="panel timeline-panel"><div class="section-toolbar"><h2>Selected conversation turns</h2><button class="jump-response action analysis-only">Jump to proposed response ↓</button></div>{history}<div class="timeline">{''.join(timeline)}</div></section>
        {context_panel(analysis,lookup)}
        {narrative('Scenario summary','scenario-summary',analysis.scenario_summary,lookup)}
        <section class="panel proposed analysis-only" id="proposed-response" tabindex="-1" aria-labelledby="proposal-title"><h2 id="proposal-title">Proposed assistant response</h2>
          <div class="response-toolbar"><strong class="target-label">Alternative for C{target.conversation} T{target.turn}</strong><span class="target-role">Observed: {target.speaker}</span><button class="view-observed action" data-target="{target.record_id}">View observed turn ↑</button><button class="copy-response action">Copy exact response</button></div>
          <details class="answer" open><summary>Full response</summary><div class="answer-body">{markdown(case.proposed,case.id.lower())}</div></details></section>
        {narrative('Response reasoning','response-reasoning',analysis.response_reasoning,lookup)}
        {narrative('Training application','training-application',analysis.training_application,lookup)}
      </div><div class="navigation-status sr-only" role="status" aria-live="polite" aria-atomic="true"></div>'''


def browser_case(case):
    """Allowlist: presentation only, never original text or private source metadata."""
    return {'id': case.id, 'title': case.title,
            'subtitle': 'Defensive monitoring' if case.id == 'CASE-01' else case.subtitle,
            'html': outcome_case_markup(case), 'proposed': case.proposed,
            'annotations': [{'id': n.id, 'title': n.title, 'categories': n.categories,
                             'anchors': [{'id': a.id, 'record': a.source_record_id, 'primary': a.primary,
                                          'reference': f'C{a.source_conversation} T{a.source_turn} · {a.speaker}'}
                                         for a in n.anchors]} for n in case.analysis.annotations]}
