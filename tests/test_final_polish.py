"""v0.4.1 contract, privacy and presentation checks; no private text literals."""
from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import json,re
import pytest
from context_safety.demonstration.polish_preview import load_approved_release, APPROVED_RELEASE_PIN
from context_safety.ui import review_app, contact
from context_safety.ui.outcome_markup import outcome_case_markup, context_panel, anchors_by_id
from context_safety.ui.evidence import coverage_audit,verify_rendered_coverage,redaction_markers
R=Path(__file__).resolve().parents[1]
O=R/'data/approved/v0.4.1'

@pytest.fixture
def preview():
    return load_approved_release(O/'preview.json')

@pytest.mark.parametrize('case',[0,1,2])
def test_complete_rendered_coverage(preview,case):
    c=preview.cases[case];audit=verify_rendered_coverage(c,outcome_case_markup(c))
    assert audit['counts']['orphans']==audit['counts']['inaccessible_items']==0
    assert len(audit['redactions'])==sum(len(m.redactions) for m in c.messages)

@pytest.mark.parametrize('attack',['missing_description','extra_highlight','missing_pointer','wrong_category','inaccessible','wrong_offset'])
def test_orphan_or_inaccessible_rendering_fails(preview,attack):
    c=preview.cases[0];html=outcome_case_markup(c)
    if attack=='missing_description':html=html.replace('id="finding-c1-defensive-goal-positive"','id="absent"')
    elif attack=='extra_highlight':html+='<mark class="passage">Invented</mark>'
    elif attack=='missing_pointer':html=html.replace('data-anchor="c1-defensive-goal-p2"','data-unlinked="c1-defensive-goal-p2"')
    elif attack=='wrong_category':html=html.replace('data-categories="positive"','data-categories="negative"')
    elif attack=='inaccessible':html=html.replace('tabindex="0"','tabindex="-1"')
    else:html=html.replace('data-passage="c1-request-span-157-242"','data-passage="c1-request-span-0-242"')
    with pytest.raises(ValueError):verify_rendered_coverage(c,html)

def test_exact_authorized_correction_only(preview):
    assert sha256((O/'preview.json').read_bytes()).hexdigest()==APPROVED_RELEASE_PIN
    assert sum(len(c.messages) for c in preview.cases)==20
    a=coverage_audit(preview.cases)
    assert a['counts']['historical_anchors']==31 and a['counts']['redacted_markers']==34
    assert a['counts']['semantic_spans']==29 and a['counts']['description_entries']==20
    for c in preview.cases:
        for m in c.messages:
            for start,end,_ in redaction_markers(m):assert m.text[start:end].startswith('[')

@pytest.mark.parametrize('attack',['source','proposal','status','classification','summary'])
def test_resealed_polish_changes_rejected(preview,tmp_path,attack):
    out=tmp_path
    data=preview.model_dump(mode='json')
    if attack=='source':data['source_sha256']='0'*64
    elif attack=='proposal':data['cases'][0]['proposed']+='Changed'
    elif attack=='status':data['research_eligible']=True
    elif attack=='classification':data['cases'][0]['analysis']['annotations'][0]['categories']=['negative']
    else:data['cases'][2]['messages'][-2]['text']='Changed summary'
    body=json.dumps(data).encode();(out/'preview.json').write_bytes(body)
    (out/'preview.manifest.json').write_text(json.dumps(dict(artifact='preview.json',version=data['version'],sha256=sha256(body).hexdigest())))
    with pytest.raises(ValueError,match='digest mismatch'):load_approved_release(out/'preview.json')

def test_four_dynamic_groups_and_true_zero_state(preview):
    c=preview.cases[0];html=context_panel(c.analysis,anchors_by_id(c.analysis))
    assert html.count('class="evidence-group ')==4
    assert 'Redacted</span>' in html and 'Selected evidence</span>' in html
    empty=c.analysis.model_copy(update={'annotations':[]})
    html=context_panel(empty,{})
    assert html.count('No evidence annotated in this category')==4
    assert html.count('0 entries')==4
    assert 'class="finding ' not in html

@pytest.mark.parametrize('value',[None,'','invalid','<script>@example.invalid','two@example.invalid\n'])
def test_contact_unavailable_no_fallback(monkeypatch,value):
    monkeypatch.setenv('CONTACT_EMAIL',value or '')
    assert contact.contact_payload(True)=={'available':False}

def test_contact_only_disclosed_after_action(monkeypatch):
    fake='test.contact@example.invalid';monkeypatch.setenv('CONTACT_EMAIL',fake)
    assert contact.contact_payload()=={'available':True}
    assert fake not in json.dumps(contact.contact_payload())
    assert contact.contact_payload(True)=={'available':True,'email':fake}
    assert fake not in review_app.about_markup()

def test_exact_about_copy_and_no_mailto():
    expected=review_app.ABOUT.read_text()
    class Text(HTMLParser):
        def __init__(self):super().__init__();self.text=[]
        def handle_data(self,data):self.text.append(data)
        def handle_endtag(self,tag):
            if tag in ('p','h1','h2'):self.text.append(' ')
    parser=Text();html=review_app.about_markup();parser.feed(html)
    plain=re.sub(r'[#*]','',expected.split('**Email:**')[0])
    assert ' '.join(''.join(parser.text).split())==' '.join(plain.split())
    assert html.count('<a ')==2 and 'mailto:' not in html
    assert 'LOG(N) Pacific' in html and 'Long Pacific' not in html


def test_authored_punctuation_scan(preview):
    # Allowlist: original display records/anchor quotes, protected responses,
    # proper research titles and historical source-matching regexes are NOT prose to edit.
    for c in preview.cases:
        a=c.analysis
        prose=[c.title,c.subtitle,c.history_note,a.scenario_background]
        prose += [s for n in a.annotations for s in (n.title,n.text,n.evidence_rationale)]
        prose += [p.text for p in a.scenario_summary+a.response_reasoning+a.training_application]
        prose += [e.text for e in a.effects]
        assert not any('\u2014' in text for text in prose)
    for name in ('review_app.py','review.js','outcome_markup.py','contact.py'):
        assert '\u2014' not in (R/'src/context_safety/ui'/name).read_text()
    assert '\u2014' not in review_app.ABOUT.read_text()
