# Seed dataset card

`data/seed_dataset.jsonl` contains 25 German ShareGPT human/assistant pairs. It covers invoice extraction, line-item rewriting, tax-clause suggestions, payment reminders and expense categorization. Domain labels are inferred heuristically and should be reviewed before using them as research labels.

The current validation run establishes parseable records and the implemented schema constraints. It does not establish legal accuracy, current tax treatment or external expert review. The origin, authorship and redistribution rights of the seed examples have not been independently documented in this repository. Resolve these before publishing the dataset under an open license.

Use this small dataset to exercise code, not to substantiate a specialized model's quality. Never treat training examples as independent test evidence. The splitter records hashes and prevents exact normalized prompt overlap, but paraphrase leakage needs manual or semantic review.

For new examples record source category, date, author/reviewer, jurisdiction, relevant official reference, allowed usage and generation model when applicable. Remove personal/customer data through an authorized process. Expert annotations should distinguish confirmed facts, assumptions and facts that require more input.

Owner update: code ownership is confirmed, while seed-data rights remain under review. See [PROVENANCE.md](PROVENANCE.md) before training or distributing derived weights.
