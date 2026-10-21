# Research foundation

This project investigates whether contextual evidence can improve the balance between legitimate assistance and safety boundaries. The publications below inform particular methods and questions. Their findings are distinct from this project's hypothesis and do not validate the complete proposed architecture.

The component letters refer to [the research architecture](ARCHITECTURE.md). Sources were checked against their publisher or author-hosted pages on October 21, 2026. This review does not acquire benchmark datasets or grant redistribution rights.

## 1. CASE-Bench: context-sensitive safety judgments

**Sun et al., ICML 2025.** [CASE-Bench: Context-Aware SafEty Benchmark for Large Language Models](https://proceedings.mlr.press/v267/sun25ab.html).

CASE-Bench formalizes contexts using Contextual Integrity and studies their effect on human safety judgments, with annotation design informed by power analysis. It also compares model judgments with human judgments.

This informs **B/C** (explicit context and classification) and **F/H** (review and study design). It is the principal methodological foundation, not a framework originated by this project. Its results do not establish that our cybersecurity interpretations, automated classifier, or cross-domain architecture improve safety.

## 2. CASE-Bench: context reliability and unresolved verification

**Sun et al., Section 6.1 and Appendix A.** [Author-hosted paper](https://hasp-lab.github.io/pubs/sun2025case.pdf).

The experiments assume reliable, verified context. The discussion identifies context validation and fabricated or contradictory information as future directions. Appendix A also notes requests that remain unsafe despite safer contexts.

This motivates separating user claims, independently supported evidence, and uncertainty in **B**, then reviewing scope and contradictions in **F/H**. It does not establish that a permission claim is trustworthy or that our system verifies real-world authorization. Investigating those distinctions is a proposed extension requiring its own evaluation.

## 3. XSTest: unnecessary refusal as a separate failure mode

**Röttger et al., NAACL 2024.** [XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models](https://aclanthology.org/2024.naacl-long.301/).

XSTest contrasts safe prompts with unsafe prompts to examine refusals triggered by sensitive topics or misleading surface wording. Its design makes unnecessary refusal inspectable rather than treating every refusal as a successful safety outcome.

It informs candidate handling categories in **C** and false-refusal analysis in **H**. It does not validate our case labels, establish authorization, or supply evidence that the proposed conversation reconstruction or model council works. Our selected cases are not an XSTest performance evaluation.

## 4. CyberSecEval 2: cybersecurity safety and utility

**Bhatt et al., 2024.** [CyberSecEval 2: A Wide-Ranging Cybersecurity Evaluation Suite for Large Language Models](https://arxiv.org/abs/2404.13161).

CyberSecEval 2 studies several cybersecurity risks and introduces false-refusal testing for benign cyber requests alongside capability and misuse assessments. This makes the safety–utility tradeoff a concrete evaluation concern.

It informs the initial cybersecurity domain in **B/C** and separate unsafe-assistance, false-refusal, and legitimate-utility questions in **H**. Its benchmark results do not establish outcomes in the dashboard's conversations, prove exploitation, or show that context-aware classification improves performance. Cybersecurity benchmark definitions should be preserved if later reused under their access and licensing conditions.

## 5. Helpful and harmless assistants: human feedback

**Bai et al., 2022.** [Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback](https://arxiv.org/abs/2204.05862).

This work studies preference modeling and reinforcement learning from human feedback for helpfulness and harmlessness, including iterative updates and competing objectives.

It informs **F** (actual reviewer feedback), **D** (response comparisons), and possible later training studies in **H**. A review process would need to identify who preferred which response and why. The paper does not make our authored alternatives human preference data, establish their correctness, or demonstrate benefits from our proposed system. The dashboard does not perform RLHF.

## 6. Direct Preference Optimization: a possible later learning method

**Rafailov et al., NeurIPS 2023.** [Direct Preference Optimization: Your Language Model is Secretly a Reward Model](https://papers.neurips.cc/paper_files/paper/2023/hash/a85b405ed65c6477a4fe8302b5e06ce7-Abstract-Conference.html).

DPO derives a preference-training objective that avoids the separately fitted reward model and reinforcement-learning stage used in a conventional RLHF pipeline.

It informs a potential connection from reviewed response comparisons in **D/F** to controlled optimization research in **H**. Before such use, this project would need independently reviewed preferences, justified sampling, and held-out validation. DPO does not establish the quality of these proposed preferences or the effectiveness of our architecture. No preference-training dataset or DPO training run is produced by this demonstration.

## 7. Deliberative Alignment: explicit policy supervision

**Guan et al., 2024; revised 2025.** [Deliberative Alignment: Reasoning Enables Safer Language Models](https://arxiv.org/abs/2412.16339).

The paper studies training models to use explicit safety specifications and reason about them before answering. Its reported findings concern the studied models and training setup.

It informs policy-aware assessment in **C**, response reasoning in **D**, and a possible supervision question in **H**. Our displayed explanations are researcher-authored analytical material, not a model's hidden reasoning or a replication of this training method. The paper does not validate the proposed model council, our reference judgments, or a reduction in harmful assistance by this project.

## How the literature bounds the proposed contribution

The proposed contribution is an evidence-linked workflow for examining conversational trajectory, authorization provenance, operational scope, and potential effects, with inspectable disagreements and human review. The dashboard illustrates these structures using approved source records; it does not test the entire architecture empirically.

The three cases provide complementary questions: candidate platform overblocking, a justified boundary despite claimed permission, and a refusal whose accompanying corrections may still provide assistance. Their evidential limits must carry into any later study.

The multi-model council, configurable redaction workflow, cross-domain generalization, and end-to-end integration remain project design proposals. None of these seven resources establishes their combined effectiveness. Future experiments require a reviewed protocol, actual specialist involvement, condition-specific references, source lineage, and separation of calibration, training, and evaluation data. More assistance or a changed recommendation is not, by itself, improvement.
