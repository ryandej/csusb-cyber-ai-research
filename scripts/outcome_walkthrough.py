"""Real Chromium acceptance for private v0.4.1. Never fetches external content."""
from pathlib import Path
from urllib.parse import urlsplit
import json,os,re
from playwright.sync_api import sync_playwright,expect
from context_safety.ui.review_app import load_catalog,PREVIEW,BASELINE,SOURCE
from context_safety.demonstration.outcome_analysis import BACKGROUND,CATEGORIES
from context_safety.demonstration.polish_preview import load_polish_preview as load_outcome_preview
from context_safety.demonstration.research import REFERENCES
from context_safety.ui.outcome_markup import browser_case

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('REVIEW_OUTPUT', str(ROOT/'local-artifacts/release-verification')))
SHOTS=OUT/'screenshots'
URL=os.environ.get('APP_URL','http://127.0.0.1:18517')
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(ROOT/'.cache/ms-playwright'))


def top(page):page.get_by_test_id('stMain').evaluate('e=>e.scrollTop=0')

def overflow(page):
 for selector in ('html','body','[data-testid="stMain"]','.review-root'):
  assert page.locator(selector).evaluate('e=>e.scrollWidth<=e.clientWidth+1'),selector


def contrast(fg,bg):
 def light(color):
  rgb=[int(c)/255 for c in re.findall(r'\d+',color)[:3]]
  return sum((c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4)*w for c,w in zip(rgb,(.2126,.7152,.0722)))
 a,b=sorted((light(fg),light(bg)));return (b+.05)/(a+.05)


def focused(locator):
 expect(locator).to_be_visible()
 for _ in range(100):
  if locator.evaluate('e=>e.getRootNode().activeElement===e'):return
  locator.page.wait_for_timeout(20)
 raise AssertionError('Navigation did not focus the selected passage/target')


def full_page(page,name):
 # Streamlit uses a fixed scroll container. Expand only that browser shell for
 # a true full-content screenshot; dashboard CSS/content/width are untouched.
 top(page)
 style=page.add_style_tag(content='''html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stMain"] {position:relative!important;height:auto!important;max-height:none!important;overflow:visible!important;}''')
 try:
  page.screenshot(path=str(SHOTS/name),full_page=True)
  assert page.evaluate('document.documentElement.scrollHeight>innerHeight')
 finally:style.evaluate('e=>e.remove()')
 top(page)


def main():
 preview=load_catalog()
 checks=[];errors=[];external=[];geometry={};ratios=[];SHOTS.mkdir(parents=True,exist_ok=True)
 def done(text):checks.append(text);print('PASS '+text,flush=True)
 def route(r):
  u=urlsplit(r.request.url)
  if (u.hostname,u.port)==(urlsplit(URL).hostname,urlsplit(URL).port):r.continue_()
  else:external.append(r.request.url);r.abort()
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  context=browser.new_context(viewport={'width':1312,'height':1199},color_scheme='dark',reduced_motion='reduce')
  context.grant_permissions(['clipboard-read','clipboard-write'],origin=URL);context.route('**/*',route)
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(URL);expect(page.locator('.timeline-item')).to_have_count(6,timeout=30000)
  expect(page.get_by_test_id('stApp')).to_have_attribute('data-test-script-state','notRunning')
  assert page.get_by_role('navigation',name='Main navigation').get_by_role('button').all_text_contents()==['Demonstration','Research','About']
  expect(page.locator('.identity strong')).to_have_text('RYAN DEJONG')
  expect(page.locator('.identity a')).to_have_attribute('href','https://github.com/ryandej')
  assert page.locator('.case-rail,.case-heading,.project-title,.comparison,.key-panel').count()==0
  assert page.locator('.project-heading h1').text_content()=='Context-Aware AI Safety'
  assert page.locator('.project-heading p').text_content()=='Cybersecurity assistance, risk, and utility'
  done('A1/A15: exact header and hierarchy; no legacy rail, duplicate heading, comparison or evaluator')
  for case in preview.cases:
   choice=page.locator(f'.case-choice[data-case="{case.id}"]')
   choice.focus();page.keyboard.press('Space')
   expect(choice).to_have_attribute('aria-pressed','true')
   assert choice.evaluate('e=>e.getRootNode().activeElement===e')
   assert page.locator('.timeline-item.selected').count()==0
   assert page.locator('.background > p').text_content()==BACKGROUND
   assert page.locator('.effect-card').count()==4
   assert page.locator('.effect-card').evaluate_all('es=>es.map(e=>e.classList[1])')==list(CATEGORIES)
   assert page.locator('.case-selection').bounding_box()['y']>page.locator('.project-heading').bounding_box()['y']
   assert page.locator('.effects').bounding_box()['y']>page.locator('.background').bounding_box()['y']
   expect(page.locator('.timeline-item')).to_have_count(len(case.messages))
   for message in case.messages:
    node=page.locator('#'+message.id)
    assert node.locator('.excerpt').evaluate('e=>e.open')==message.start_expanded
    assert node.locator('.timeline-marker > strong').text_content()==f'C{message.conversation} T{message.turn}'
    assert not re.search(r'\bC\d+\s+T\d+\b',node.locator('.speech').text_content())
   for group in page.locator('.history-group').all():group.evaluate('e=>e.open=true')
   for message in case.messages:
    node=page.locator('#'+message.id);details=node.locator('.excerpt')
    if not details.evaluate('e=>e.open'):details.locator('summary').click()
    expect(details.locator('.expand-label')).to_have_text('Minimize')
    assert details.locator('.full-excerpt').text_content()==message.text
    assert details.locator('.preview-text').text_content()==message.text[:205]
    details.locator('summary').focus();page.keyboard.press('Enter')
    expect(details.locator('summary')).to_have_attribute('aria-expanded','false')
    expect(details.locator('.expand-label')).to_have_text('Expand')
   done(f'{case.id} A2–A6: exact background, four effects, all source records, role/kind/chips, exact full display and keyboard expansion')
   choice.click()
   for group in page.locator('.evidence-group').all():group.evaluate('e=>e.open=true')
   for note in case.analysis.annotations:
    # Every primary and secondary pointer must navigate to its actual passage.
    for anchor in note.anchors:
     button=page.locator(f'.finding[data-anchor="{anchor.id}"]') if anchor.primary else page.locator(f'.support-links [data-anchor="{anchor.id}"]')
     button=button.first
     button.focus();page.keyboard.press('Enter')
     node=page.locator('#'+anchor.source_record_id)
     expect(node).to_have_attribute('aria-current','true')
     expect(node.locator('.expand-label')).to_have_text('Minimize')
     mark=node.locator(f'.source-body [data-anchors~="{anchor.id}"]').first
     focused(mark);expect(mark).to_be_in_viewport()
     marks=node.locator(f'.source-body [data-anchors~="{anchor.id}"]')
     assert ''.join(marks.all_text_contents())==anchor.display_text
     assert page.locator('.timeline-item.selected').count()==1
     expected_linked={a.source_record_id for a in note.anchors}-{anchor.source_record_id}
     assert set(page.locator('.timeline-item.linked').evaluate_all('es=>es.map(e=>e.id)'))==expected_linked
     assert node.locator('.speech').evaluate('e=>getComputedStyle(e).outlineWidth')=='3px'
     assert node.locator('.speech').evaluate('e=>getComputedStyle(e).outlineColor')=='rgb(255, 176, 32)'
     colors=mark.evaluate('e=>{const s=getComputedStyle(e);return [s.color,s.backgroundColor,s.borderBottomColor]}')
     ratio=contrast(colors[0],colors[1]);assert ratio>=4.5,(note.id,ratio)
     ratios.append(dict(case=case.id,anchor=anchor.id,category=note.categories[0],text_ratio=ratio))
     # Repeated activation must navigate again, including a previously expanded source.
     button.click();focused(mark);expect(mark).to_be_in_viewport()
    if case.id=='CASE-02' and note.id=='c2-monitoring-positive':
     page.locator(f'.finding[data-note="{note.id}"]').first.click()
     focused(page.locator('#c2-response .active-passage').first)
     page.screenshot(path=str(SHOTS/'case-02-selected-label.png'))
   # All four effect cards and all turn chips, including multi-category inference.
   for cat in CATEGORIES:
    page.locator(f'.effect-card.{cat}').click()
    mark=page.locator('.source-body .active-passage').first;focused(mark)
    expect(mark).to_have_attribute('data-selected-category',cat)
    page.screenshot(path=str(SHOTS/f'{case.id.lower()}-passage-{cat}.png'))
   for group in page.locator('.history-group').all():group.evaluate('e=>e.open=true')
   for chip in page.locator('.turn-chips button').all():
    target=chip.get_attribute('data-anchor');category=chip.get_attribute('data-category')
    chip.focus();page.keyboard.press('Space')
    mark=page.locator(f'.source-body .active-passage[data-anchors~="{target}"]').first;focused(mark)
    expect(mark).to_have_attribute('data-selected-category',category)
   done(f'{case.id} A7/A8: every primary/secondary passage, repeated selection, four card colors, all turn chips, exact highlighted text and focus')
   # Observation preserves source bytes/order and expansion state but removes interpretive presentation.
   states=page.locator('.excerpt').evaluate_all('es=>es.map(e=>e.open)')
   ids=page.locator('[data-message]').evaluate_all('es=>es.map(e=>e.id)')
   switch=page.locator('button[data-mode="observation"]');switch.focus();page.keyboard.press('Enter')
   expect(switch).to_have_attribute('aria-pressed','true')
   for selector in ('.effects','.turn-chips','.context-panel','.scenario-summary','.proposed','.response-reasoning','.training-application'):
    assert not any(el.is_visible() for el in page.locator(selector).all()),selector
   assert states==page.locator('.excerpt').evaluate_all('es=>es.map(e=>e.open)')
   assert ids==page.locator('[data-message]').evaluate_all('es=>es.map(e=>e.id)')
   assert page.locator('.timeline-item.selected').count()==0
   assert page.locator('.source-body mark').count()==0
   if case.id=='CASE-02':
    choice.click();top(page);page.screenshot(path=str(SHOTS/'observation-mode.png'))
   page.locator('button[data-mode="analysis"]').focus();page.keyboard.press('Space')
   assert page.locator('.effects').is_visible() and page.locator('.context-panel').is_visible()
   done(f'{case.id} A9: Observation hides interpretations and preserves source chronology/content; Analysis restores')
   # Response controls and narrative citations.
   choice.click()
   jump=page.locator('.jump-response');jump.focus();page.keyboard.press('Enter')
   focused(page.locator('.proposed'));expect(page.locator('.target-label')).to_be_in_viewport()
   target=case.analysis.response_target
   assert page.locator('.target-label').text_content()==f'Alternative for C{target.conversation} T{target.turn}'
   assert page.locator('.answer').evaluate('e=>e.open')
   page.screenshot(path=str(SHOTS/f'{case.id.lower()}-proposed-target.png'))
   page.locator('.copy-response').focus();page.keyboard.press('Space')
   expect(page.locator('.copy-response')).to_have_text('Copied')
   assert page.evaluate('navigator.clipboard.readText()')==case.proposed
   for button in page.locator('[data-copy]').all():
    expected=page.locator('#'+button.get_attribute('data-copy')).text_content();button.click()
    expect(button).to_have_text('Copied');assert page.evaluate('navigator.clipboard.readText()')==expected
   observed=page.locator('.view-observed');observed.focus();page.keyboard.press('Enter')
   node=page.locator('#'+target.record_id);focused(node)
   expect(node.locator('.speech-role')).to_contain_text('Platform block' if target.speaker=='Platform' else 'Assistant')
   if case.id=='CASE-01':page.screenshot(path=str(SHOTS/'case-01-platform-target.png'))
   for selector in ('.scenario-summary','.response-reasoning','.training-application'):
    for button in page.locator(selector+' .source-link').all():
     button.click();focused(page.locator(f'.source-body .active-passage[data-anchors~="{button.get_attribute("data-anchor")}"]').first)
   # Default ordering measured after reset, without selected earlier history inflating the timeline.
   choice.click();positions={s:page.locator(s).bounding_box()['y'] for s in ('.timeline-panel','.scenario-summary','.proposed','.response-reasoning','.training-application')}
   assert list(positions.values())==sorted(positions.values())
   geometry[case.id]=positions
   if case.id=='CASE-02':
    page.locator('.scenario-summary').evaluate("e=>e.scrollIntoView({block:'start'})")
    page.screenshot(path=str(SHOTS/'case-02-summary-and-response.png'))
    choice.click();page.locator('.effect-card.neutral').click()
    focused(page.locator('#c2-request .active-passage').first)
    page.screenshot(path=str(SHOTS/'case-02-selected-label.png'))
   if case.id=='CASE-03':
    expect(page.locator('#c3-reuse .source-kind')).to_have_text('Researcher summary')
    page.locator('#c3-simulation').evaluate("e=>e.scrollIntoView({block:'start'})")
    page.screenshot(path=str(SHOTS/'case-03-sequence.png'))
   done(f'{case.id} A10–A14: cited summary/reasoning/training, correct observed role/target, keyboard jump/view, exact full-response and code copying')
  # Rapid clicks/case changes invalidate pending source navigation; keyboard Tab cancels stale focus.
  for case in preview.cases:
   page.locator(f'.case-choice[data-case="{case.id}"]').click()
   page.locator('.finding').first.evaluate('e=>e.click()')
  page.locator('.case-choice[data-case="CASE-01"]').click()
  expect(page.locator('.timeline-item.selected')).to_have_count(0)
  for group in page.locator('.evidence-group').all():group.evaluate('e=>e.open=true')
  first=page.locator('.finding').first;second=page.locator('.finding').nth(1)
  first.focus();page.keyboard.press('Enter');second.focus();page.keyboard.press('Enter')
  focused(page.locator('#c1-diagram .active-passage').first)
  page.keyboard.press('Escape');expect(page.locator('.timeline-item.selected')).to_have_count(0)
  done('A8: rapid case/passage changes, pending-focus cancellation and Escape clearing')
  # Clipboard denial retains exact selectable text rather than copying rendered prose.
  page.locator('.jump-response').click();focused(page.locator('.proposed'))
  page.evaluate("()=>{window.savedWrite=Object.getPrototypeOf(navigator.clipboard).writeText;Object.getPrototypeOf(navigator.clipboard).writeText=async()=>{throw new Error('Local denial test')};}")
  page.locator('.copy-response').click();expect(page.locator('.copy-fallback')).to_be_visible()
  assert page.locator('.copy-fallback').input_value()==preview.cases[0].proposed
  page.locator('.view-observed').focus();expect(page.locator('.copy-fallback')).to_have_count(0)
  page.evaluate("Object.getPrototypeOf(navigator.clipboard).writeText=window.savedWrite;delete window.savedWrite")
  done('Exact selectable fallback when clipboard permission is denied')
  # Reference and About tabs are unchanged, with no hidden evaluator controls.
  page.get_by_role('button',name='Research',exact=True).click()
  expect(page.locator('.research-foundation h1')).to_have_text('Research Foundation')
  assert page.locator('.research-foundation a').evaluate_all('es=>es.map(e=>e.href)')==[u for _,u,_ in REFERENCES]
  assert page.locator('.research-foundation p').count()==7
  top(page);page.screenshot(path=str(SHOTS/'research.png'))
  page.get_by_role('button',name='About',exact=True).click();expect(page.locator('.about h1')).to_have_text('About the Research')
  assert page.locator('.about a').count()==2
  top(page);page.screenshot(path=str(SHOTS/'about.png'))
  assert not page.get_by_role('combobox').count() and not page.get_by_test_id('stFileUploader').count()
  done('A15: exact seven Research references, approved About, visitor-only routes')
  page.get_by_role('button',name='Demonstration',exact=True).click();expect(page.locator('.case-main')).to_have_attribute('data-case','CASE-01')
  for width,height in [(1312,1199),(1512,1100),(390,844),(320,844)]:
   page.set_viewport_size({'width':width,'height':height})
   for case in preview.cases:
    page.locator(f'.case-choice[data-case="{case.id}"]').click();top(page);overflow(page)
    name=f'{case.id.lower()}-{width}x{height}'
    page.screenshot(path=str(SHOTS/(name+'-viewport.png')))
    full_page(page,name+'-full.png')
    if case.id=='CASE-01':
     alias={1312:'opening-1312x1199.png',1512:'opening-1512x1100.png',390:'mobile-390.png',320:'narrow-320.png'}[width]
     top(page);page.screenshot(path=str(SHOTS/alias))
    boxes={s:page.locator(s).bounding_box() for s in ('.topbar','.project-heading','.case-choices','.background','.effects','.timeline-panel','.context-panel','.proposed')}
    geometry[name]=boxes
    if width>900:
     assert boxes['.context-panel']['x']>boxes['.timeline-panel']['x']+boxes['.timeline-panel']['width']
     total=boxes['.context-panel']['width']+boxes['.timeline-panel']['width']
     assert .66<boxes['.timeline-panel']['width']/total<.70
    else:assert boxes['.context-panel']['y']>boxes['.timeline-panel']['y']
    page.locator('.effect-card.neutral').click();focused(page.locator('.source-body .active-passage').first);overflow(page)
    page.screenshot(path=str(SHOTS/(name+'-selected.png')))
    page.locator('.jump-response').click();focused(page.locator('.proposed'));overflow(page)
    page.screenshot(path=str(SHOTS/(name+'-response.png')))
   done(f'Responsive {width}×{height}: all three viewport/full-content captures, evidence and response navigation; no overflow')
  # New context with light OS theme, reduced motion, touch: default remains dark.
  light=browser.new_context(viewport={'width':390,'height':844},color_scheme='light',has_touch=True,reduced_motion='reduce')
  light.route('**/*',route);phone=light.new_page();phone.on('pageerror',lambda e:errors.append(str(e)))
  phone.goto(URL);expect(phone.locator('.timeline-item')).to_have_count(6,timeout=30000)
  assert phone.locator('.review-root').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(12, 18, 27)'
  phone.locator('.case-choice[data-case="CASE-02"]').tap();phone.locator('.effect-card.negative').tap()
  focused(phone.locator('.source-body .active-passage').first);overflow(phone)
  phone.screenshot(path=str(SHOTS/'mobile-touch-light-preference.png'))
  done('Dark default under light OS preference, reduced motion and mobile touch')
  # Actual shadow DOM contains only the explicit safe browser allowlist.
  payload=json.dumps([browser_case(c) for c in preview.cases],ensure_ascii=False)
  for case in preview.cases:
   for m in case.messages:
    assert m.request_reference not in payload and m.spans[0].sha256 not in payload
  assert not errors,errors
  assert not external,external
  done('No private source metadata in component payload; zero external page requests and uncaught JS errors')
  (OUT/'browser-verification.json').write_text(json.dumps(dict(checks=checks,page_errors=errors,external_requests=external,geometry=geometry,contrast_samples=ratios),indent=2)+'\n')
  browser.close()
 print(f'{len(checks)} browser groups passed.',flush=True)

if __name__=='__main__':main()
