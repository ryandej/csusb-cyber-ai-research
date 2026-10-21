// Local presentation only: no inference, network fetch, source execution or storage.
export default function(component) {
  const {data, parentElement, setTriggerValue} = component;
  const root = parentElement.querySelector('.review-root');
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let generation = 0;
  let mode = 'analysis';
  let escapeHandler;
  root.innerHTML = `<header class="topbar"><div class="identity"><strong>RYAN DEJONG</strong><a href="https://github.com/ryandej" target="_blank" rel="noopener noreferrer">https://github.com/ryandej</a></div><nav aria-label="Main navigation">${['Demonstration','Research','About'].map(v=>`<button data-nav="${v}" ${v===data.view?'aria-current="page"':''}>${v}</button>`).join('')}</nav></header><div class="review-content"></div>`;
  root.querySelectorAll('[data-nav]').forEach(button => button.addEventListener('click', () => {
    if (button.dataset.nav !== data.view) setTriggerValue('navigate', button.dataset.nav);
  }));
  const content = root.querySelector('.review-content');
  if (data.view === 'About') {
    content.innerHTML = data.about;
    const controls=content.querySelector('.contact-controls');
    if(controls) {
      const contact=data.contact || {};
      controls.innerHTML='<strong>Email</strong> '+(!contact.available ? '<span>Email currently unavailable</span>' : contact.email ?
        `<span class="contact-address" tabindex="0">${esc(contact.email)}</span><button class="action copy-email">Copy email</button><button class="action hide-email">Hide email</button>` :
        '<button class="action reveal-email" aria-describedby="contact-help">Reveal email</button><span id="contact-help" class="sr-only">Request the contact address from the local server.</span>')+'<span class="contact-status" role="status" aria-live="polite"></span>';
      controls.querySelector('.reveal-email')?.addEventListener('click',()=>setTriggerValue('reveal_contact',true));
      controls.querySelector('.hide-email')?.addEventListener('click',()=>{
        controls.replaceChildren();setTriggerValue('hide_contact',true);
      });
      controls.querySelector('.copy-email')?.addEventListener('click',async()=>{
        const status=controls.querySelector('.contact-status');
        try {
          await navigator.clipboard.writeText(contact.email);
          if(status.isConnected) status.textContent='Email copied';
        } catch {
          if(status.isConnected) status.textContent='Select the email address to copy it manually';
        }
      });
      if(contact.just_hidden) {
        controls.querySelector('.contact-status').textContent='Email hidden';
        requestAnimationFrame(()=>{if(controls.isConnected)controls.querySelector('.reveal-email')?.focus();});
      }
      if(contact.email) {
        controls.querySelector('.contact-status').textContent='Email revealed';
        requestAnimationFrame(()=>{if(controls.isConnected)controls.querySelector('.copy-email')?.focus();});
      }
    }
  }
  else if (data.view === 'Research') content.innerHTML = data.research;
  else if (!data.cases?.length) {
    content.innerHTML = '<main class="about"><h1>Local evidence preview</h1><p>The local conversation preview is unavailable.</p></main>';
  } else {
    content.innerHTML = `<main class="dashboard"><section class="project-heading"><h1>Context-Aware LLM Safety Classifier</h1><p>Reducing unnecessary refusals while maintaining safeguards against harmful assistance.</p></section><section class="case-selection" aria-labelledby="choose-heading"><div class="selection-heading"><h2 id="choose-heading">Choose a conversation</h2><div class="mode-switch" role="group" aria-label="Presentation mode"><button data-mode="analysis" aria-pressed="true">Analysis</button><button data-mode="observation" aria-pressed="false">Observation</button></div></div><nav class="case-choices" aria-label="Conversation cases">${data.cases.map(c=>`<button class="case-choice" data-case="${esc(c.id)}" aria-controls="selected-case"><strong>${esc(c.title)}</strong><span>${esc(c.subtitle)}</span></button>`).join('')}</nav></section><div class="case-main" id="selected-case"></div></main>`;
    const main = root.querySelector('.case-main');
    const dashboard = root.querySelector('.dashboard');
    let current;
    const activeElement = () => root.getRootNode().activeElement;
    function announce(text) {
      const status = main.querySelector('.navigation-status');
      status.textContent = '';
      queueMicrotask(()=> { if(status.isConnected) status.textContent = text; });
    }
    function focusAfterLayout(target, message) {
      const mine = ++generation;
      const focus = activeElement();
      requestAnimationFrame(()=>requestAnimationFrame(()=>{
        if (mine !== generation || !target.isConnected || activeElement() !== focus) return;
        // Instant navigation also honors reduced-motion users and avoids stale smooth scrolls.
        const record=target.closest('[data-message]');
        const nearStart=record && target.matches('.passage') && target.getBoundingClientRect().top-record.getBoundingClientRect().top<220;
        (nearStart?record:target).scrollIntoView({block:'start',behavior:'instant'});
        target.focus({preventScroll:true});
        announce(message);
      }));
    }
    function mountSource(details) {
      const body = details.querySelector('.source-body');
      body.replaceChildren(details.querySelector('.source-template').content.cloneNode(true));
      // Observation removes annotation semantics for assistive technology too.
      if(mode==='observation') {
        body.querySelectorAll('mark').forEach(mark=>mark.replaceWith(document.createTextNode(mark.textContent)));
        body.querySelectorAll('.redacted-status').forEach(span=>{
          span.removeAttribute('role');span.removeAttribute('tabindex');span.removeAttribute('data-anchors');
        });
      }
    }
    function updateExpansion(details) {
      const body = details.querySelector('.source-body');
      if (details.open && !body.firstChild) mountSource(details);
      details.querySelector('.expand-label').textContent = details.open ? 'Minimize' : 'Expand';
      details.querySelector('summary').setAttribute('aria-expanded',String(details.open));
    }
    function openRecord(record) {
      let ancestor = record.parentElement;
      while (ancestor && ancestor !== main) {
        if (ancestor.matches('details.history-group')) ancestor.open = true;
        ancestor = ancestor.parentElement;
      }
      const details = record.querySelector('details.excerpt');
      details.open = true;
      updateExpansion(details);
    }
    function clearSelection() {
      generation += 1;
      main.querySelectorAll('[data-message]').forEach(el=>{
        el.classList.remove('selected','linked'); el.removeAttribute('aria-current');
        el.querySelector('.evidence-label').hidden = true;
        el.querySelector('.linked-label').hidden = true;
      });
      main.querySelectorAll('.passage,.redacted-status').forEach(mark=>{
        mark.classList.remove('active-passage'); mark.removeAttribute('data-selected-category');
      });
      main.querySelectorAll('[data-anchor]').forEach(button=>button.setAttribute('aria-pressed','false'));
      main.querySelector('.proposed')?.classList.remove('navigation-target');
      main.querySelectorAll('.finding-group').forEach(el=>el.classList.remove('selected-explanation'));
      const options=main.querySelector('.evidence-options');if(options){options.hidden=true;options.replaceChildren();}
    }
    function selectPassage(noteId, anchorId, category, direction='source') {
      if (mode !== 'analysis') return;
      const note = current.annotations.find(a=>a.id===noteId);
      const anchor = note?.anchors.find(a=>a.id===anchorId);
      if (!anchor) return;
      category=note.categories.includes(category)?category:note.categories[0];
      clearSelection();
      const target = main.querySelector(`[data-message="${anchor.record}"]`);
      const linked = new Set(note.anchors.map(a=>a.record));
      main.querySelectorAll('[data-message]').forEach(el=>{
        const primary = el === target;
        el.classList.toggle('selected',primary);
        el.classList.toggle('linked',!primary && linked.has(el.dataset.message));
        el.querySelector('.evidence-label').hidden = !primary;
        el.querySelector('.linked-label').hidden = primary || !linked.has(el.dataset.message);
        if(primary) el.setAttribute('aria-current','true');
      });
      openRecord(target);
      const marks = [...target.querySelectorAll('.source-body [data-anchors]')].filter(m=>m.dataset.anchors.split(' ').includes(anchorId));
      marks.forEach(mark=>{
        mark.classList.add('active-passage');
        mark.dataset.selectedCategory = note.categories.includes(category) ? category : note.categories[0];
      });
      main.querySelectorAll('[data-anchor]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.anchor===anchorId)));
      const explanation=main.querySelector(`#finding-${noteId}-${category}`);
      explanation.closest('.evidence-group').open=true;
      explanation.classList.add('selected-explanation');
      main.querySelectorAll('.finding').forEach(b=>b.setAttribute('aria-pressed',String(b.parentElement===explanation)));
      const destination=direction==='explanation'?explanation.querySelector('.finding'):marks[0];
      if(destination) focusAfterLayout(destination,`${category}. ${anchor.reference}. ${note.title}. ${direction==='explanation'?'Explanation':'Evidence'} selected.`);
    }
    function explainPassage(passage) {
      if(mode!=='analysis')return;
      const anchorIds=passage.dataset.anchors.split(' ');
      const choices=current.annotations.flatMap(note=>note.anchors.filter(a=>anchorIds.includes(a.id))
        .flatMap(anchor=>note.categories.map(category=>({note,anchor,category}))));
      if(choices.length===1) {
        const {note,anchor,category}=choices[0];selectPassage(note.id,anchor.id,category,'explanation');return;
      }
      // Multi-category passages expose every rationale instead of silently choosing one.
      clearSelection();
      const turn=passage.closest('[data-message]');turn.classList.add('selected');turn.setAttribute('aria-current','true');
      turn.querySelector('.evidence-label').hidden=false;
      const options=main.querySelector('.evidence-options');options.hidden=false;
      options.innerHTML='<p>This passage supports more than one interpretation. Choose an explanation:</p>';
      for(const {note,anchor,category} of choices) {
        const button=document.createElement('button');button.className='action '+category;
        button.textContent=`${category[0].toUpperCase()+category.slice(1)}: ${note.title}`;
        button.addEventListener('click',()=>selectPassage(note.id,anchor.id,category,'explanation'));
        options.append(button);
      }
      focusAfterLayout(options.querySelector('button'),'Choose a category and explanation for this source passage.');
    }
    main.addEventListener('click',event=>{
      const passage=event.target.closest('.source-body [data-anchors]');if(passage)explainPassage(passage);
    });
    main.addEventListener('keydown',event=>{
      if(event.key==='Enter'||event.key===' ') {
        const passage=event.target.closest('.source-body [data-anchors]');
        if(passage){event.preventDefault();explainPassage(passage);}
      }
    });
    async function copyText(text, button, fallbackNode) {
      try {
        await navigator.clipboard.writeText(text);
        if(button.isConnected) { button.textContent='Copied'; announce('Exact response text copied.'); }
      } catch {
        // A selectable textarea preserves the exact string, including Markdown and whitespace.
        const field=document.createElement('textarea');field.value=text;field.className='copy-fallback';
        field.setAttribute('aria-label','Exact text; press Control+C or Command+C to copy');
        (fallbackNode || button.parentElement).append(field);field.focus();field.select();
        button.textContent='Select to copy';announce('Clipboard unavailable. Exact text selected for manual copying.');
        field.addEventListener('blur',()=>field.remove(),{once:true});
      }
    }
    function applyMode() {
      clearSelection();
      dashboard.dataset.mode = mode;
      root.querySelectorAll('button[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
      // Restore annotations without modifying source content, order, or expansion state.
      main.querySelectorAll('.analysis-only').forEach(el=>{el.hidden=mode==='observation';});
      main.querySelectorAll('details.excerpt').forEach(details=>{
        if(details.querySelector('.source-body').firstChild) mountSource(details);
      });
      announce(mode==='observation'?'Observation: source timeline only.':'Analysis: proposed interpretations restored.');
    }
    function renderCase(id, navigate=false) {
      const chosen=data.cases.find(c=>c.id===id);if(!chosen)return;
      generation += 1;current=chosen;
      main.innerHTML=current.html;main.dataset.case=id;
      root.querySelectorAll('.case-choice').forEach(b=>{
        b.setAttribute('aria-current',String(b.dataset.case===id));b.setAttribute('aria-pressed',String(b.dataset.case===id));
      });
      main.querySelectorAll('details.excerpt').forEach(details=>{
        updateExpansion(details);details.addEventListener('toggle',()=>updateExpansion(details));
      });
      main.querySelectorAll('[data-anchor]').forEach(button=>button.addEventListener('click',()=>selectPassage(button.dataset.note,button.dataset.anchor,button.dataset.category || button.closest('.finding-group')?.dataset.category)));
      main.querySelector('.jump-response').addEventListener('click',()=>{
        clearSelection();const target=main.querySelector('.proposed');
        target.classList.add('navigation-target');target.querySelector('.answer').open=true;
        focusAfterLayout(target,`${current.title}: proposed assistant response. ${target.querySelector('.target-label').textContent}.`);
      });
      main.querySelector('.view-observed').addEventListener('click',event=>{
        clearSelection();const target=main.querySelector(`[data-message="${event.currentTarget.dataset.target}"]`);
        openRecord(target);target.classList.add('selected');target.setAttribute('aria-current','true');
        target.querySelector('.evidence-label').hidden=false;
        focusAfterLayout(target,`Observed ${target.querySelector('.speech-role').firstChild.textContent.trim()}, ${target.querySelector('.timeline-marker strong').textContent}.`);
      });
      main.querySelector('.copy-response').addEventListener('click',event=>copyText(current.proposed,event.currentTarget));
      main.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',()=>copyText(main.querySelector(`[id="${button.dataset.copy}"]`).textContent,button)));
      applyMode();
      if(navigate) {
        // Keep selectors and page heading stable; a pointer click does not focus a giant heading.
        root.querySelector('.case-selection').scrollIntoView({block:'start',behavior:'instant'});
        announce(`${current.title} selected. ${mode==='analysis'?'Analysis':'Observation'} view.`);
      }
    }
    root.querySelectorAll('.case-choice').forEach(b=>b.addEventListener('click',()=>renderCase(b.dataset.case,true)));
    root.querySelectorAll('button[data-mode]').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.mode;applyMode();}));
    escapeHandler=event=>{
      if(event.key==='Escape') { clearSelection();announce('Evidence selection cleared.'); }
    };
    root.addEventListener('keydown',escapeHandler);
    renderCase(data.cases[0].id);
  }
  return () => { root.replaceChildren(); generation += 1; if(escapeHandler)root.removeEventListener('keydown',escapeHandler); };
}
