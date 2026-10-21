# Context-Aware LLM Safety Classifier: Research Architecture

*Architecture under active development*

The [README diagram](../README.md#proposed-classifier-architecture) describes a proposed cross-domain research system. Cybersecurity provides the initial testbed. This document specifies intended responsibilities and information boundaries; it does not introduce implemented model integrations, an automated classifier, or an approved experiment protocol.

## Current implementation and intended interfaces

| Component | Demonstrated today | Planned interface or capability |
| --- | --- | --- |
| A. Conversation ingestion and reconstruction | A fixed, approved set of source records with original turn IDs and selected branch history. | Import transcripts and reconstruct their conversation structure. |
| B. Context reconstruction and interpretation | Shared background, linked source passages, and researcher-authored contextual interpretations. | Build evidence-aware contextual representations from imported records. |
| C. AI-assisted classification | Authored effect categories on turns and spans, linked to explanations. | Automated classification with configurable taxonomies and uncertainty. |
| D. Scenario generation and response analysis | Approved background, summaries, alternatives, reasoning, and training panels. | Produce reviewable, source-grounded drafts with explicit authorship. |
| E. Sensitive-data management | Fixed approved redactions and visible omission markers. | Detection, proposed redactions, permission-controlled original/redacted views, and exports. |
| F. Human-in-the-loop review | Evidence inspection and bidirectional navigation; fixed author analysis. | Editable labels, overrides, reviewer feedback, and adjudication history. |
| G. Multi-model council | No model connections or council execution. | Local/cloud adapters and competing analyst, specialist, critic, and judge perspectives. |
| H. Controlled evaluation | Software preservation and interaction tests. | Empirical studies with reviewed references, explicit denominators, and held-out evaluation. |

The public dashboard performs no inference. Owner approval of display content is distinct from independent specialist review of a reference annotation.

## A. Conversation ingestion and reconstruction

Accept authorized conversation exports and transcripts. Preserve speaker roles, chronological order, stable message identities, and separate branches rather than flattening alternatives into a single conversation. Retain tool interactions, attachment references, timestamps, source formats, and acquisition provenance where available. Missing metadata should remain explicitly missing.

The proposed output is a versioned conversation record plus a branch graph and an import report. Original source bytes remain protected. A transformation must identify its source, parser version, changes, and any ambiguity; successful parsing alone does not establish source reliability.

## B. Context reconstruction and interpretation

Build a contextual representation of conversation history, trajectory, subject matter, relevant domain expertise, technical environment, requested operation, and possible consequences. Relevant user-provided background or profile information may inform interpretation, but collecting identities or inferring sensitive traits is not a prerequisite.

Every contextual assertion should distinguish **user-supplied**, **algorithm-inferred**, **researcher-interpreted**, and **independently supported** information. Independently verified authorization would require an identifiable evidence source, verification method, time, and operational scope. A claim of permission or expertise does not satisfy that requirement. A trusted record within a simulated scenario is only trusted within that simulation.

Preserve contradictions, uncertainty, and missing evidence. Authorization evidence, permitted scope, and safety appropriateness remain separate dimensions. Additional context need not change the appropriate response; some requests remain inappropriate despite claimed permission.

## C. AI-assisted classification

Proposed algorithms would attach classifications to turns and exact source spans, assess contextual safety and utility, and provide inspectable evidence-linked explanations. Taxonomy identifiers, versions, categories, subcategories, uncertainty, and applicable policy should accompany each output. Explanations are reviewable claims, not proof of correctness or access to a model's hidden reasoning.

The current dashboard uses **Positive, Negative, Neutral, and Unintended** potential-effect categories. These describe possible effects of assistance. **Redacted** remains a separate display status. Future handling categories may address overrefusal, legitimate safe assistance, appropriate safety boundaries, and unsafe assistance risk; adopting them requires definitions and calibration, not simply renaming the current categories.

## D. Scenario generation and response analysis

Create separate, linked analytical objects for Scenario background, Scenario summary, source passages, potential effects, proposed alternatives, response reasoning, and potential training or evaluation applications. An alternative must identify the original assistant turn or platform event it addresses.

Each draft should retain its author type, model or researcher identity where actually known, version, source references, and review status. A generated passage must not be represented as a source quotation. A summary must preserve evidential limits and distinguish claims, observed behavior, and hypothesized outcomes. Proposed preferences require review before any future training use.

## E. Sensitive-data management

Place access and redaction decisions around ingestion, review, and export. Proposed capabilities include PII and sensitive-data detection, reviewer approval of redactions, authorized original/redacted view toggles, and controlled export manifests. Detection results would be proposals requiring scrutiny; they would not by themselves grant permission to disclose content.

Keep protected originals separate from display derivatives, with stable redaction mappings and lineage. A public export must not recover omitted material from hidden client payloads. This planned configurable workflow is distinct from the demonstration's fixed approved redactions, which remain unchanged and offer no original-source toggle.

## F. Human-in-the-loop review

Reviewers should be able to inspect supporting evidence, correct classifications, refine labels, add custom categories and subcategories, override model judgments, and compare revised interpretations. Preserve the prior state, actual reviewer involvement, rationale, disagreement, and adjudication rather than silently overwriting a prediction.

The proposed review record links the reviewed artifact/version, reviewer role, decision, time, and supporting evidence. Author-proposed annotations, completed specialist reviews, and adjudicated references need distinct statuses. No synthetic reviewer judgments may substitute for actual review.

## G. Multi-model council

A proposed adapter interface would support authorized local or cloud models. A contextual analyst reconstructs the exchange; a domain specialist examines technical implications; a safety critic challenges assistance and evidence; a separate judge or adjudicator compares interpretations. Humans supervise their disagreements and may reject all proposed judgments.

The council interacts with classification and response analysis rather than forming a mandatory serial pipeline. Preserve each model's identity, settings, available context, raw output, parsed output, evidence references, and critique. Different models can share assumptions or errors; agreement is not sufficient evidence of correctness. The degree of independence must be documented, not inferred from a role name.

## H. Controlled evaluation and iterative improvement

Investigate false refusal and unsafe assistance separately, alongside legitimate task completion, domain usefulness, reviewer agreement, confidence calibration, and appropriately designed satisfaction/productivity studies. A stated confidence is not a calibrated probability. Counts, eligibility criteria, denominators, uncertainty, and failures should remain visible; no composite safety score is proposed here.

Future studies need independently reviewed condition-specific references, including cases where appropriate handling is invariant. Separate calibration from held-out evaluation, preserve source-native benchmark definitions and licensing, and prevent overlap among training, tuning, and evaluation families. Compare contextual and isolated-request methods only within an approved protocol; this roadmap does not amend previously frozen study decisions or authorize experiments.

Feedback may motivate new taxonomy, classification, or response-selection versions. Evaluation data must not silently become tuning data: record protocol amendments and use an appropriate new holdout when needed.

## Proposed data flow and provenance boundaries

| Interface | Intended information contract |
| --- | --- |
| Source → ingestion | Source ID/version, access authority, integrity digest, raw-record reference, parser/import report. |
| Ingestion → permitted view | Message and branch IDs, roles, ordering, available tool/attachment/time metadata, redaction decisions and view permissions. |
| Permitted view → context | Source-anchored assertions with origin, evidence status, scope, contradictions, and uncertainty. |
| Context → classification | Context snapshot, taxonomy/policy version, turn/span references, raw and parsed outputs, output validation status. |
| Classification ↔ review/council | Proposed judgments, individual critiques, actual reviewer actions, alternatives, and adjudication history. |
| Analysis → response comparison | Source-linked narrative components, explicit target, authorship, proposed response version, and review status. |
| Reviewed artifacts → evaluation | Eligible split, frozen references, model/run settings, errors, denominator definitions, and lineage. |

These are design interfaces, not newly implemented schemas. Source text is untrusted data, never executable instructions. Model adapters would require separate authorization, server-side credentials, bounded inputs, usage limits, and isolation from protected sources. Public source excerpts, proposed analyses, and future evaluation data must retain distinct provenance.
