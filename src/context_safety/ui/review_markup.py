"""Escaped presentation for the local evidence preview. No source text embedded here."""
from html import escape
import re
from context_safety.demonstration.preview import PreviewCase


def inline(text):
    # Escape first. Supported formatting is deliberately limited to the approved answers.
    safe = escape(text)
    safe = re.sub(r'`([^`]+)`', r'<code>\1</code>', safe)
    return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', safe)


def excerpt_prefix(text, limit):
    """Shorten visible source wording without leaving cut Markdown delimiters."""
    plain = re.sub(r'\*\*|`', '', text.strip())
    return plain if len(plain) <= limit else plain[:limit].rsplit(' ', 1)[0] + ' …'


def markdown(text, prefix):
    """Render paragraphs/lists/code without enabling HTML, links, or script execution."""
    chunks = re.split(r'(```[^\n]*\n.*?\n```)', text, flags=re.S)
    out, code_index = [], 0
    for chunk in chunks:
        if chunk.startswith('```'):
            code = chunk.split('\n', 1)[1].rsplit('\n```', 1)[0]
            code_index += 1
            key = f'{prefix}-code-{code_index}'
            out.append(f'<div class="code-wrap"><button class="copy" data-copy="{key}" aria-label="Copy code {code_index}">Copy</button><pre><code id="{key}">{escape(code)}</code></pre></div>')
        else:
            for paragraph in chunk.strip().split('\n\n'):
                if not paragraph:
                    continue
                if paragraph.startswith('`') and paragraph.endswith('`') and '\n' not in paragraph:
                    code_index += 1
                    key = f'{prefix}-code-{code_index}'
                    out.append(f'<div class="code-wrap command"><button class="copy" data-copy="{key}" aria-label="Copy command {code_index}">Copy</button><pre><code id="{key}">{escape(paragraph[1:-1])}</code></pre></div>')
                elif re.match(r'^\d+\. ', paragraph):
                    items = re.split(r'\n(?=\d+\. )', paragraph)
                    out.append('<ol>'+''.join('<li>'+inline(re.sub(r'^\d+\. ', '', item))+'</li>' for item in items)+'</ol>')
                else:
                    out.append('<p>'+inline(paragraph)+'</p>')
    return ''.join(out)


def message_markup(message):
    ref = f'C{message.conversation} T{message.turn}'
    text = message.text  # Preserve all source whitespace, punctuation and code.
    prefix = text[:205]
    expanded = getattr(message, 'start_expanded', False)
    label = 'Minimize' if expanded else 'Expand'
    source_kind = {'verbatim': '', 'redacted': 'Redacted source', 'summary': 'Researcher summary'}[message.kind]
    speaker = 'Platform block' if message.role == 'Platform' else message.role
    body = (f'<details class="excerpt"{" open" if expanded else ""}>'
            f'<summary><span class="excerpt-preview"><span class="preview-text">{escape(prefix)}</span>'
            f'{"<span class=ellipsis> …</span>" if len(text) > len(prefix) else ""}</span>'
            f'<span class="expand-label">{label}</span></summary>'
            f'<template class="source-template"><div class="full-excerpt">{escape(text)}</div></template>'
            f'<div class="source-body"></div></details>')
    return (f'<article class="timeline-item {message.role.lower()}{" critical" if message.critical else ""}" id="{message.id}" '
            f'data-message="{message.id}" aria-labelledby="{message.id}-ref {message.id}-speaker">'
            f'<div class="timeline-marker"><span class="dot"></span><strong id="{message.id}-ref">{ref}</strong>'
            f'<small>{escape(message.stage)}</small><small class="source-kind">{escape(source_kind)}</small></div>'
            f'<div class="speech"><div class="speech-role" id="{message.id}-speaker">{escape(speaker)}'
            f'<span class="evidence-label" hidden>Selected evidence</span></div>{body}</div></article>')


def case_markup(case: PreviewCase):
    timeline, grouped = [], []
    def flush():
        if grouped:
            group = grouped[0].group
            title = 'Earlier context' if group == 'earlier' else 'Follow-up exchange'
            refs = ', '.join(dict.fromkeys(f'C{m.conversation} T{m.turn}' for m in grouped))
            timeline.append(f'<details class="history-group"><summary>{title} <span>{escape(refs)}</span></summary>'+''.join(message_markup(m) for m in grouped)+'</details>')
            grouped.clear()
    for m in case.messages:
        if m.group != 'main':
            if grouped and grouped[-1].group != m.group:
                flush()
            grouped.append(m)
        else:
            flush()
            timeline.append(message_markup(m))
    flush()
    findings = ''.join(f'<button class="finding {a.tone}" data-annotation="{a.id}" aria-pressed="false"><span class="finding-title">{escape(a.label)}</span><span>{escape(a.text)}</span></button>' for a in case.annotations)
    keys = ''
    for a in case.annotations:
        support = next(m for m in case.messages if m.id == a.supports[0])
        excerpt = excerpt_prefix(support.text, 85)
        refs = ', '.join(dict.fromkeys(f'C{m.conversation} T{m.turn}' for m in case.messages if m.id in a.supports))
        keys += (f'<button class="key-passage {a.tone}" data-annotation="{a.id}" aria-pressed="false"><span class="dot"></span>'
                 f'<strong>{escape(a.label)}</strong><small>{escape(refs)}</small><span class="key-quote">{inline(excerpt)}</span></button>')
    observed_class = 'observed appropriate' if case.id == 'CASE-02' else 'observed'
    shared = getattr(case, 'shared_background', '')
    shared_markup = (f'<details class="shared-context"><summary>Earlier scenario context</summary>'
                     f'<p>{escape(shared)}</p></details>') if shared else ''
    history = getattr(case, 'history_note', '')
    history_markup = f'<p class="history-note">{escape(history)}</p>' if history else ''
    return f'''
    <section class="case-heading"><h1>{escape(case.title)}</h1><p>{escape(case.subtitle)}</p></section>
    <div class="evidence-grid">
      <section class="conversation-column">
        <section class="panel background"><h2><span class="icon">▤</span> Scenario background</h2><div class="background-body"><div><p>{escape(case.background)}</p>{history_markup}{shared_markup}</div><aside><strong>{escape(case.focus)}</strong><span>Selected decision</span></aside></div></section>
        <section class="panel timeline-panel"><h2>Selected conversation turns</h2><div class="timeline">{''.join(timeline)}</div></section>
      </section>
      <aside class="analysis-column">
        <section class="panel context-panel"><h2><span class="icon">⌕</span> Context analysis</h2><div class="findings">{findings}</div></section>
        <section class="panel key-panel"><h2>Key passages</h2><div class="key-list">{keys}</div><div class="selected-evidence" aria-live="polite"></div></section>
      </aside>
    </div>
    <div class="response-grid">
      <section class="panel proposed"><h2><span class="icon">◇</span> Proposed assistant response <span class="tag">Proposed</span></h2><details class="answer" open><summary>Full response</summary><div class="answer-body">{markdown(case.proposed,case.id.lower())}</div></details></section>
      <section class="panel comparison"><h2><span class="icon">♧</span> Response comparison and training application</h2><div class="comparison-body"><div class="outcomes"><section class="preferred"><h3>Proposed</h3><p>{escape(case.preferred)}</p></section><section class="{observed_class}"><h3>{'Observed platform block' if case.id=='CASE-01' else 'Observed model response'}</h3><p>{escape(case.observed)}</p></section></div><h3>Researcher assessment</h3><p>{escape(case.assessment)}</p><h3>How this could inform AI training</h3><p>{escape(case.training)}</p></div></section>
    </div>'''
