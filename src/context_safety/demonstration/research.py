"""Brief source-supported explanations. All links verified 2026-10-20.

Sources extend the approved literature review; no benchmark text or data copied.
"""
REFERENCES = [
    ("CASE-Bench · Sun et al., ICML 2025", "https://proceedings.mlr.press/v267/sun25ab.html",
     "Context changed human safety judgments in the paper's study. Its framework builds on Contextual Integrity; this project builds on that foundation."),
    ("CASE-Bench context-reliability assumption · §6.1 and Appendix A", "https://hasp-lab.github.io/pubs/sun2025case.pdf",
     "The study assumes reliable, verified context and identifies context validation as future work. It does not establish that a user's permission claim should be trusted."),
    ("XSTest · Röttger et al., NAACL 2024", "https://aclanthology.org/2024.naacl-long.301/",
     "Tests with safe requests and unsafe contrasts document exaggerated safety behavior: refusing benign requests is a distinct problem from failing to refuse harmful ones."),
    ("CyberSecEval 2 · Bhatt et al., 2024", "https://arxiv.org/abs/2404.13161",
     "The cybersecurity evaluation suite examines security risks and false refusals of benign cyber requests. Its safety–utility tradeoff motivates checking both kinds of error."),
    ("Helpful and harmless assistants · Bai et al., 2022", "https://arxiv.org/abs/2204.05862",
     "This work studies preference modeling and reinforcement learning from human feedback to train for helpfulness and harmlessness. A preferred response is not automatically a universal safety standard."),
    ("Direct Preference Optimization · Rafailov et al., NeurIPS 2023", "https://papers.neurips.cc/paper_files/paper/2023/hash/a85b405ed65c6477a4fe8302b5e06ce7-Abstract-Conference.html",
     "DPO optimizes a language model using preference comparisons without the separate reward-model and reinforcement-learning stages of a conventional RLHF pipeline."),
    ("Deliberative Alignment · Guan et al., 2024", "https://arxiv.org/abs/2412.16339",
     "This work trains models with explicit safety specifications and reasoning about them. It motivates studying policy-aware supervision; our authored annotations are not a model's hidden reasoning or a replication of that method."),
]

TRAINING_METHODS = [
    ("Supervised fine-tuning", "After review, context paired with an appropriate response could illustrate a desired behavior. This demonstration performs no training."),
    ("Preference-based training", "Experts could compare alternatives. Direct Preference Optimization (DPO) uses preference pairs; reinforcement learning from human feedback (RLHF) typically learns a reward model before policy optimization. Our author preferences are not human feedback."),
    ("Policy-aware safety supervision", "Reviewers could relate decisions to an explicit policy, including evidence quality, scope limits, and permissible assistance. Policy agreement would need to be established."),
    ("Context-sensitive evaluation", "Independent held-out cases could test both unnecessary refusal and inappropriate compliance, including cases whose appropriate handling stays unchanged."),
]
