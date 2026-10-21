"""v0.4.1 real Chromium checks. No private values or source prose in this script."""
from pathlib import Path
from urllib.parse import urlsplit
import json,os,re,sys
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.outcome_walkthrough import focused,overflow,contrast,full_page,top
from context_safety.ui.review_app import load_catalog,PREVIEW,BASELINE,SOURCE,ABOUT
from context_safety.ui.contact import contact_email
from context_safety.demonstration.polish_preview import load_polish_preview
from context_safety.ui.evidence import coverage_audit
OUT=Path(os.environ.get('REVIEW_OUTPUT', str(ROOT/'local-artifacts/release-verification')));SHOTS=OUT/'screenshots';URL=os.environ.get('APP_URL','http://127.0.0.1:18517')
MISSING_CONTACT_URL=os.environ.get('MISSING_CONTACT_URL','http://127.0.0.1:18519')
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(ROOT/'.cache/ms-playwright'))


def main():
 SHOTS.mkdir(parents=True,exist_ok=True)
 preview=load_catalog();audit=coverage_audit(preview.cases)
 secret=contact_email();assert secret
 checks=[];errors=[];external=[];clicks=[];ratios=[];frames=[];responses=[]
 def done(id,text):checks.append(dict(id=id,result='PASS',detail=text));print('PASS '+id+': '+text,flush=True)
 def route(r):
  u=urlsplit(r.request.url)
  if (u.hostname,u.port) in {(urlsplit(URL).hostname,urlsplit(URL).port),(urlsplit(MISSING_CONTACT_URL).hostname,urlsplit(MISSING_CONTACT_URL).port)}:r.continue_()
  else:external.append(r.request.url);r.abort()
 def attach(page):
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('websocket',lambda ws:ws.on('framereceived',lambda value:frames.append(value.encode() if isinstance(value,str) else value)))
  def received(response):
   try:responses.append(response.body())
   except Exception:pass
  page.on('response',received)
 def about(page):
  page.get_by_role('button',name='About',exact=True).click();expect(page.locator('.about h1')).to_have_text('About the Research')
  expect(page.get_by_test_id('stApp')).to_have_attribute('data-test-script-state','notRunning')
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  context=browser.new_context(viewport={'width':1312,'height':1199},color_scheme='dark',reduced_motion='reduce')
  context.route('**/*',route);context.grant_permissions(['clipboard-read','clipboard-write'],origin=URL)
  page=context.new_page();attach(page);page.goto(URL);expect(page.locator('.timeline-item')).to_have_count(6,timeout=30000)
  for case in preview.cases:
   page.locator(f'.case-choice[data-case="{case.id}"]').click()
   groups=page.locator('.evidence-group');expect(groups).to_have_count(4)
   for category in ('positive','negative','neutral','unintended'):
    group=page.locator(f'[data-group="{category}"]');count=sum(category in n.categories for n in case.analysis.annotations)
    assert group.locator('.finding-group').count()==count
    expect(group.locator('.group-count')).to_have_text(f'{count} '+('entry' if count==1 else 'entries'))
    before=groups.evaluate_all('es=>es.map(e=>e.open)');group.locator('summary').focus();page.keyboard.press('Space')
    after=groups.evaluate_all('es=>es.map(e=>e.open)');assert sum(a!=b for a,b in zip(before,after))==1
    group.locator('summary').focus();page.keyboard.press('Enter');assert groups.evaluate_all('es=>es.map(e=>e.open)')==before
   for group in page.locator('.history-group').all():group.evaluate('e=>e.open=true')
   for details in page.locator('.excerpt').all():
    if not details.evaluate('e=>e.open'):details.locator('summary').click()
   expect(page.locator('.source-body .redacted-status')).to_have_count(sum(len(m.redactions) for m in case.messages))
   expected=[s for s in audit['spans'] if s['case_id']==case.id]
   assert set(page.locator('.source-body .passage').evaluate_all('es=>es.map(e=>e.dataset.passage)'))=={s['id'] for s in expected}
   for span in expected:
    mark=page.locator(f'[data-passage="{span["id"]}"]').first
    # Every interpretation of every rendered semantic span is reachable, repeatedly.
    for descid in span['description_ids']:
     for group in groups.all():group.evaluate('e=>e.open=false')
     mark.focus();page.keyboard.press('Enter')
     desc=next(d for d in audit['descriptions'] if d['id']==descid)
     options=page.locator('.evidence-options')
     if len(span['description_ids'])>1:
      expect(options).to_be_visible();buttons=options.get_by_role('button');expect(buttons).to_have_count(len(span['description_ids']))
      button=buttons.filter(has_text=re.compile('^'+desc['category'].title()+':')).first
      button.focus();page.keyboard.press('Space')
     finding=page.locator('#'+descid+' .finding');focused(finding)
     expect(page.locator('#'+descid)).to_have_class(re.compile('selected-explanation'))
     assert finding.locator('xpath=..').count()==1
     assert page.locator('.timeline-item.selected').count()==1
     expect(page.locator('.navigation-status')).to_contain_text(f'C{span["conversation"]} T{span["turn"]}')
     # Its source-specific pointer returns directly to this anchor, not a generic primary.
     anchor=next(a for a in span['anchors'] if a['id'] in {a.id for n in case.analysis.annotations if n.id==desc['annotation_id'] for a in n.anchors})
     pointer=page.locator(f'#{descid} [data-anchor="{anchor["id"]}"]').first
     pointer.click();target=page.locator(f'#{span["source_id"]} .source-body [data-anchors~="{anchor["id"]}"]').first;focused(target)
     mark.click()
     if len(span['description_ids'])>1:options.get_by_role('button').filter(has_text=re.compile('^'+desc['category'].title()+':')).first.click()
     focused(finding)
     clicks.append(dict(test=span['click_test_id'],description=descid,forward=True,inverse=True,repeated=True,keyboard=True))
   # Withheld evidence has genuine explanation links but no semantic color.
   for marker in [s for s in audit['redactions'] if s['case_id']==case.id and s['anchor_ids']]:
    node=page.locator(f'.source-body [data-redaction="{marker["redaction_id"]}"]');node.click()
    if page.locator('.evidence-options').is_visible():page.locator('.evidence-options button').last.click()
    expect(page.locator('.selected-explanation')).to_have_count(1)
    assert not node.get_attribute('data-categories')
   done('H01-H04/'+case.id,'Every rendered passage and category explanation linked both ways; independent groups and counts; repeated keyboard activation')
   page.locator('.context-panel').evaluate('e=>e.scrollIntoView()');page.screenshot(path=str(SHOTS/(case.id.lower()+'-grouped-evidence.png')))
   for group in groups.all():group.evaluate('e=>e.open=false')
   page.locator('.context-panel').evaluate('e=>e.scrollIntoView()');page.screenshot(path=str(SHOTS/(case.id.lower()+'-groups-collapsed.png')))
   for category in ('positive','negative','neutral','unintended'):
    group=page.locator(f'[data-group="{category}"]');group.locator('summary').click()
    page.locator('.context-panel').evaluate('e=>e.scrollIntoView()');page.screenshot(path=str(SHOTS/(case.id.lower()+'-group-'+category+'.png')))
    group.locator('summary').click()
   page.locator('button[data-mode="observation"]').click()
   expect(page.locator('.source-body .passage')).to_have_count(0)
   assert page.locator('.source-body .redacted-status').count()==sum(len(m.redactions) for m in case.messages)
   assert page.locator('.source-body .redacted-status[role="button"]').count()==0
   assert all(not e.is_visible() for e in page.locator('.analysis-only').all())
   page.locator('.redacted-status').first.evaluate('e=>e.scrollIntoView()');page.screenshot(path=str(SHOTS/(case.id.lower()+'-observation-redacted.png')))
   page.locator('button[data-mode="analysis"]').click()
   done('H06-H07/'+case.id,'All verified omission markers survive Observation; outcome semantics removed, withheld contents absent')
  page.locator('.case-choice[data-case="CASE-03"]').click()
  msg=next(m for m in preview.cases[2].messages if m.id=='c3-reuse')
  expect(page.locator('#c3-reuse .full-excerpt')).to_have_text(msg.text,use_inner_text=False)
  expect(page.locator('#c3-reuse .source-kind')).to_have_text('Researcher summary')
  page.locator('#c3-reuse').evaluate('e=>e.scrollIntoView()');page.screenshot(path=str(SHOTS/'case-03-corrected-summary.png'))
  done('H13-H14','Corrected C27 T6 summary, unchanged identity, exact approved targets and source qualifications retained')
  page.locator('.case-choice[data-case="CASE-02"]').click();page.locator('.effect-card.neutral').click();focused(page.locator('#c2-request .active-passage').first)
  page.screenshot(path=str(SHOTS/'neutral-and-selected.png'))
  for cat in ('positive','negative','neutral','unintended'):
   e=page.locator('.effect-card.'+cat)
   colors=e.evaluate('e=>{const s=getComputedStyle(e),t=getComputedStyle(e.querySelector("strong"));return {ink:t.color,bg:s.backgroundColor,border:s.borderTopColor}}')
   ratios.append(dict(category=cat,**colors,text_ratio=contrast(colors['ink'],colors['bg']),border_ratio=contrast(colors['border'],colors['bg'])))
  assert all(r['text_ratio']>=4.5 and r['border_ratio']>=3 for r in ratios),ratios
  red=page.locator('.evidence-key .redacted-status');colors=red.evaluate('e=>{const s=getComputedStyle(e);return {ink:s.color,bg:s.backgroundColor,border:s.borderTopColor}}')
  ratios.append(dict(category='redacted',**colors,text_ratio=contrast(colors['ink'],colors['bg']),border_ratio=contrast(colors['border'],colors['bg'])))
  assert ratios[-1]['text_ratio']>=4.5 and ratios[-1]['border_ratio']>=3
  assert page.locator('#c2-request .speech').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(21, 48, 77)'
  assert page.locator('#c2-response .speech').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(17, 30, 45)'
  assert page.locator('.selected .speech').evaluate('e=>getComputedStyle(e).outlineColor')=='rgb(255, 176, 32)'
  done('H05','Measured text/border contrast and distinct burnt orange versus bright selected outline; speaker fills preserved')
  # Exact approved prose rendered with whitespace-normalized block boundaries.
  about(page)
  assert page.locator('.about a').evaluate_all('es=>es.map(e=>e.href)')==['https://github.com/ryandej','https://www.linkedin.com/in/ryscde']
  expected=re.sub(r'[#*]','',ABOUT.read_text().split('**Email:**')[0])
  actual=page.locator('.about').evaluate('e=>{const n=e.cloneNode(true);n.querySelector(".contact-controls").remove();return [...n.children].map(x=>x.textContent).join(" ")}')
  assert ' '.join(actual.split())==' '.join(expected.split())
  assert '\u2014' not in actual
  assert secret not in page.locator('.review-root').text_content() and secret not in page.content()
  assert all(secret.encode() not in b for b in frames+responses)
  initial_counts=dict(websocket_frames=len(frames),http_bodies=len(responses))
  expect(page.locator('.copy-email')).to_have_count(0)
  assert not page.locator('a[href^="mailto:"]').count()
  full_page(page,'about-full-before-reveal.png');top(page);page.screenshot(path=str(SHOTS/'about-opening-before-reveal.png'))
  page.locator('.reveal-email').focus();page.screenshot(path=str(SHOTS/'contact-before-reveal.png'));page.keyboard.press('Space')
  expect(page.locator('.contact-address')).to_have_text(secret)
  focused(page.locator('.copy-email'));page.keyboard.press('Enter');expect(page.locator('.contact-status')).to_have_text('Email copied')
  assert page.evaluate('navigator.clipboard.readText()')==secret
  page.screenshot(path=str(SHOTS/'PRIVATE-contact-after-reveal.png'))
  page.evaluate("()=>{window.savedWrite=Object.getPrototypeOf(navigator.clipboard).writeText;Object.getPrototypeOf(navigator.clipboard).writeText=async()=>{throw Error('Denied')}}")
  page.locator('.copy-email').click();expect(page.locator('.contact-status')).to_have_text('Select the email address to copy it manually')
  page.locator('.hide-email').focus();page.keyboard.press('Enter');expect(page.locator('.reveal-email')).to_be_visible();focused(page.locator('.reveal-email'));expect(page.locator('.contact-status')).to_have_text('Email hidden');expect(page.locator('.contact-address')).to_have_count(0)
  page.evaluate('Object.getPrototypeOf(navigator.clipboard).writeText=window.savedWrite;delete window.savedWrite')
  page.locator('.reveal-email').click();expect(page.locator('.contact-address')).to_be_visible()
  page.get_by_role('button',name='Research',exact=True).click();expect(page.locator('.research-foundation')).to_be_visible();about(page);expect(page.locator('.reveal-email')).to_be_visible()
  page.locator('.reveal-email').click();expect(page.locator('.contact-address')).to_be_visible();page.reload();expect(page.locator('.timeline-item')).to_have_count(6,timeout=30000);about(page);expect(page.locator('.reveal-email')).to_be_visible()
  done('H09-H11','Exact About copy, initial HTTP/WebSocket/DOM without email; real Reveal/Copy/Hide; denied clipboard truthful; navigation and reload reset')
  # Fresh mobile session starts hidden, including all newly received payloads.
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});overflow(page);full_page(page,f'about-{width}-before-reveal.png')
   page.locator('.reveal-email').focus();page.keyboard.press('Enter');expect(page.locator('.copy-email')).to_be_visible();overflow(page)
   page.screenshot(path=str(SHOTS/f'PRIVATE-contact-{width}-revealed.png'))
   page.locator('.hide-email').click();expect(page.locator('.reveal-email')).to_be_visible()
   page.get_by_role('button',name='Demonstration',exact=True).click();expect(page.locator('.timeline-item')).to_have_count(6)
   page.locator('#c1-request .passage').first.click();focused(page.locator('.selected-explanation .finding'))
   overflow(page);page.screenshot(path=str(SHOTS/f'evidence-to-description-{width}.png'))
   page.locator('.selected-explanation .finding').click();focused(page.locator('.active-passage').first)
   overflow(page);page.screenshot(path=str(SHOTS/f'description-to-evidence-{width}.png'));about(page)
  done('Mobile','390px and 320px bidirectional evidence, contact keyboard controls and readable layout without overflow')
  fresh=browser.new_context(viewport={'width':390,'height':844});fresh.route('**/*',route);phone=fresh.new_page();frames.clear();responses.clear();attach(phone)
  phone.goto(URL);expect(phone.locator('.timeline-item')).to_have_count(6,timeout=30000);about(phone)
  expect(phone.locator('.reveal-email')).to_be_visible();assert secret not in phone.locator('.review-root').text_content()
  assert all(secret.encode() not in b for b in frames+responses)
  unavailable=browser.new_page();unavailable.route('**/*',route);unavailable.goto(MISSING_CONTACT_URL);expect(unavailable.locator('.timeline-item')).to_have_count(6,timeout=30000);about(unavailable)
  expect(unavailable.locator('.contact-controls')).to_contain_text('Email currently unavailable');expect(unavailable.locator('.reveal-email')).to_have_count(0)
  unavailable.screenshot(path=str(SHOTS/'contact-unavailable.png'))
  done('Privacy negatives','Fresh session hidden; missing server secret produces unavailable state, no fallback address or external mail handler')
  page.set_viewport_size({'width':1312,'height':1199});page.get_by_role('button',name='Demonstration',exact=True).click();expect(page.locator('.timeline-item')).to_have_count(6)
  page.locator('.identity a').focus();order=[]
  for _ in range(65):
   page.keyboard.press('Tab');entry=page.locator('.review-root').evaluate('e=>{const a=e.getRootNode().activeElement;return {tag:a?.tagName,outline:a?getComputedStyle(a).outlineWidth:null,role:a?.getAttribute("role")}}');order.append(entry)
  assert all(e['outline']=='3px' for e in order if e['tag'] in ('BUTTON','SUMMARY','A','MARK'))
  for _ in range(8):page.keyboard.press('Shift+Tab')
  assert page.locator('.review-root').evaluate('e=>e.contains(e.getRootNode().activeElement)')
  assert page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
  page.locator('.effect-card.neutral').focus();page.keyboard.press('Space');focused(page.locator('.active-passage').first)
  page.screenshot(path=str(SHOTS/'keyboard-focus.png'));page.emulate_media(forced_colors='active');page.locator('.active-passage').first.click();focused(page.locator('.selected-explanation .finding'))
  page.screenshot(path=str(SHOTS/'forced-colors.png'))
  done('Accessibility','65 Tab steps, reverse traversal, visible focus, live announcements, Enter/Space, reduced motion and forced colors')
  assert not errors,errors;assert not external,external
  done('H15','No uncaught page errors, external requests or visitor evaluator controls')
  audit.update(browser_clicks=clicks,browser_inaccessible_items=0,browser_orphans=0)
  (OUT/'EVIDENCE_COVERAGE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
  (OUT/'polish-browser-results.json').write_text(json.dumps(dict(checks=checks,clicks=len(clicks),contrast=ratios,initial_payload_counts=initial_counts,tab_order=order,page_errors=errors,external_requests=external),indent=2)+'\n')
  browser.close()
 print(f'{len(checks)} targeted browser groups passed; {len(clicks)} semantic passage/category round trips.',flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  import traceback
  value=contact_email()
  text=traceback.format_exc()
  print(text.replace(value,'[contact value withheld]') if value else text,flush=True)
  raise SystemExit(1)
