# Context-Aware LLM Safety Classifier

**Reducing unnecessary refusals while maintaining safeguards against harmful assistance.**

### [Launch the Live Interactive Demo](https://context-aware-ai-safety.streamlit.app/)

**Research and development by [Ryan DeJong](https://github.com/ryandej)**

This ongoing research project develops context-aware LLM safety classification methods. Its objective is to distinguish legitimate assistance, unnecessary refusal, appropriate safety boundaries, and potentially harmful assistance using contextual evidence. The public Streamlit application demonstrates the current research workflow and source-grounded case analysis; the complete automated classifier remains under research and development.

## Research objective

A request's meaning can depend on the conversation leading up to it, the operation being requested, and the reliability and scope of supporting evidence. The proposed classifier examines these dimensions together while keeping user claims, algorithmic interpretations, and independently supported evidence distinct.

**Research hypothesis:** Context-aware safety mechanisms can reduce unnecessary refusals without increasing harmful assistance when compared with evaluating requests primarily in isolation.

This hypothesis requires empirical validation. Cybersecurity is the initial testbed because dual-use requests make the tension between legitimate assistance and harmful capabilities particularly visible. The intended classifier is cross-domain.

## Proposed classifier architecture

### Context-Aware LLM Safety Classifier: Research Architecture

*Architecture under active development*

The diagram describes the proposed system. The current dashboard displays source-linked analytical structures; the automated pipeline and interacting review components below are planned.

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 300, "nodeSpacing": 25, "rankSpacing": 35}, "themeVariables": {"fontSize": "16px"}}}%%
flowchart TB
    accTitle: Context-Aware LLM Safety Classifier: Research Architecture
    accDescr: Proposed top-to-bottom flow from ingestion through protected views, evidence-linked analysis and evaluation. Human reviewers and a model council exchange critiques and corrections with the analysis. Evaluation feeds protocol-guided improvements back into analysis.
    A["A · Conversation ingestion<br/>Roles, branches, provenance"]
    E["E · Sensitive-data management<br/>Redactions and authorized views"]
    subgraph WORK["Analysis and oversight"]
        direction LR
        subgraph ANALYSIS["Analytical flow"]
            direction TB
            B["B · Context reconstruction<br/>Evidence, scope, uncertainty"]
            C["C · AI-assisted classification<br/>Turn and span labels + evidence"]
            D["D · Scenario / response analysis<br/>Alternatives and reasoning"]
            B --> C --> D
        end
        subgraph REVIEW["Review team"]
            direction TB
            F["F · Human-in-the-loop review<br/>Corrections and decision provenance"]
            G["G · Multi-model council<br/>Analyst, specialist, critic, judge"]
            F <-. adjudication .-> G
        end
        ANALYSIS <-. evidence and critique .-> REVIEW
    end
    H["H · Controlled evaluation<br/>Safety, utility, agreement, calibration"]

    A --> E --> WORK --> H
    H -. protocol-guided improvement .-> WORK

    classDef analytical fill:#e8f1fb,stroke:#326797,color:#142d45,stroke-width:1.5px
    classDef review fill:#f1eafb,stroke:#73509a,color:#35204c,stroke-width:1.5px
    classDef governance fill:#e8f4ef,stroke:#34735b,color:#173c2d,stroke-width:1.5px
    class A,B,C,D analytical
    class F,G review
    class E,H governance
    style WORK fill:#ffffff,stroke:#a1acb9,color:#263447
    style ANALYSIS fill:#f7faff,stroke:#8da9c4,color:#142d45
    style REVIEW fill:#faf7ff,stroke:#a48bbd,color:#35204c
```

Solid arrows describe the primary information flow; dashed arrows describe review and feedback. Model agreement would be evidence to inspect, not proof of correctness.

### Architecture components

| Component | Proposed responsibility |
| --- | --- |
| **A. Ingestion** | Preserve conversations, separate branches, speaker roles, tool interactions, attachments, timestamps, and available provenance. |
| **B. Context** | Reconstruct the trajectory, domain knowledge, relevant user-provided background, authorization evidence, operational scope, and uncertainty. |
| **C. Classification** | Assign configurable turn- and span-level safety/utility labels with evidence-linked explanations. |
| **D. Response analysis** | Keep Scenario background, summary, source passages, potential effects, proposed responses, reasoning, and training/evaluation applications distinct. |
| **E. Sensitive data** | Detect sensitive material, propose redactions, authorize original/redacted views, and control exports while preserving protected originals. |
| **F. Human review** | Correct labels, add categories, override judgments, compare interpretations, and retain reviewer decision provenance. |
| **G. Model council** | Compare analyst, domain specialist, safety critic, and judge perspectives under human oversight. |
| **H. Evaluation** | Study false refusal, unsafe assistance, legitimate task completion, usefulness, reviewer agreement, calibration, satisfaction, and productivity. |

[Architecture details, proposed interfaces, and implementation status →](docs/ARCHITECTURE.md)

## Current research demonstration

The accepted v0.4.1 dashboard presents three source-grounded cases with original turn references, approved redactions, and researcher-authored analysis. The walkthrough below shows the application with its updated project header. No live classification or response generation runs behind these views. Open an image for full-size source text.

### 1. Establish the scenario

The shared Scenario background introduces the user's described situation before the reader examines individual turns. Case selection and four potential-effect categories orient the analysis without treating the user's account as independently verified.

[![Updated dashboard showing case selection, the shared Scenario background, four potential-effect cards, and the timeline/evidence layout](docs/images/readme/01-dashboard-overview.png)](docs/images/readme/01-dashboard-overview.png)

### 2. Inspect the source timeline

Connected turns preserve chronology and speaker identity. Expand a record to inspect its text and turn identifier. Redactions and omissions remain visible; a researcher summary is identified separately from a source quotation.

[![Connected Case 2 timeline with User and Assistant records, C4 turn identifiers, expanded source text, redactions, and selected evidence](docs/images/readme/02-source-timeline.png)](docs/images/readme/02-source-timeline.png)

### 3. Follow the evidence

Select a passage to reach its explanation, or follow an explanation back to the supporting passage. Collapsible groups organize **Positive, Negative, Neutral, and Unintended** potential effects. **Redacted** is a separate source-display status, not an effect classification or a judgment about the user.

[![A selected Case 2 passage beside its linked Context and evidence explanation, with grouped effect categories and the selected-evidence outline](docs/images/readme/03-context-evidence.png)](docs/images/readme/03-context-evidence.png)

### 4. Examine the response analysis

The Scenario summary synthesizes the cited record. The proposed response names the original turn it addresses; Response reasoning explains the proposed choice. Training application discusses possible later uses. These are separate analytical components, and an authored alternative is not an observed model output.

[![Focused view of the complete proposed assistant response targeting C4 T83, with its original-turn link and copy control](docs/images/readme/04-response-analysis-crop.png)](docs/images/readme/04-response-analysis.png)

The focused view shows the authored alternative. [Open the complete response-analysis capture](docs/images/readme/04-response-analysis.png) to inspect the original target, Scenario summary, Response reasoning, and separate Training application together.

### 5. Read without analytical overlays

Observation mode removes the analytical overlays while retaining the source chronology and redaction indicators. It supports independent inspection of what the selected records actually show.

[![Observation mode in the updated application, showing original conversation records and redaction markers without analytical overlays](docs/images/readme/05-observation-mode.png)](docs/images/readme/05-observation-mode.png)

## Three cybersecurity research cases

| Case | Source-grounded interpretation |
| --- | --- |
| **Overrefusal · C8 T2** | A platform-level cybersecurity block, not an assistant-written refusal. It is candidate overblocking rather than a conclusively demonstrated safety failure. |
| **Safety Boundary · C4 T83–T84** | The model appropriately challenged unsafe measures despite claimed authorization. The proposed alternative explores clearer, safely bounded practical assistance; the original response is not inherently a failure. |
| **Unsafe Assistance Risk · C27 T5–T6** | A refusal appeared alongside potentially useful implementation corrections. The follow-up reused a corrected service identifier; it establishes neither successful exploitation nor use of every earlier suggestion. |

These cases motivate questions and make evidence inspectable. They do not establish performance across domains or validate the proposed classifier.

## Research and development roadmap

| Phase | Scope | Status |
| --- | --- | --- |
| **1. Existing demonstration** | Source-grounded dashboard, contextual evidence visualization, linked analysis, approved redactions, and response reasoning. | Accepted v0.4.1 foundation; live demo available. |
| **2. Conversation ingestion and editing** | Import, provenance tracking, branch reconstruction, editable annotations, and configurable taxonomies. | Planned. |
| **3. Automated contextual analysis** | AI-assisted interpretation and classification, scenario generation, human review, and configurable sensitive-data management. | Research and development planned. |
| **4. Multi-model council** | Model integrations, collaborative interpretation, independent judging, disagreement analysis, and human-guided adjudication. | Planned. |
| **5. Controlled experimentation** | Safety and utility evaluation, annotation reliability, calibration, and potential training or optimization methods. | Requires a reviewed study protocol and empirical validation. |

## Research foundation

[CASE-Bench](https://proceedings.mlr.press/v267/sun25ab.html) motivates context-sensitive safety judgments. Its [context-reliability discussion](https://hasp-lab.github.io/pubs/sun2025case.pdf) makes the distinction between reliable evidence and a user's permission claim central to this project's proposed extension.

[XSTest](https://aclanthology.org/2024.naacl-long.301/) motivates testing unnecessary refusal, while [CyberSecEval 2](https://arxiv.org/abs/2404.13161) informs separate cybersecurity safety and utility assessments. Work on [helpfulness and harmlessness](https://arxiv.org/abs/2204.05862), [Direct Preference Optimization](https://papers.neurips.cc/paper_files/paper/2023/hash/a85b405ed65c6477a4fe8302b5e06ce7-Abstract-Conference.html), and [Deliberative Alignment](https://arxiv.org/abs/2412.16339) informs possible future feedback, preference, and policy-aware supervision methods.

[Read the literature-to-architecture review](docs/RESEARCH_FOUNDATION.md) for each source's contribution and limits. These publications do not validate this project's complete architecture or demonstrate its effectiveness.

## Researcher

**Ryan DeJong** conducts independent AI security research focused on LLM safety and security evaluation and context-sensitive analysis of dual-use requests. The project draws on volunteer research through California State University, San Bernardino's Center for Cyber and AI; it does not imply university sponsorship or endorsement.

[GitHub](https://github.com/ryandej) · [LinkedIn](https://www.linkedin.com/in/ryscde)

## Technical documentation

[Architecture](docs/ARCHITECTURE.md) · [Research foundation](docs/RESEARCH_FOUNDATION.md) · [Local development](docs/DEVELOPMENT.md) · [Deployment](DEPLOYMENT.md) · [Verification and preservation](VERIFICATION.md)
