# Evidence required for a public release

1. **Software:** run dependency checks, seed validation and the full pytest suite. Exercise the demo with both an unavailable backend and a real model. GitHub Actions must pass on the supported Python versions.
2. **Data:** document rights and provenance; obtain accounting review; record domain balance, split hashes and leakage checks. Include cases for ambiguous VAT, missing facts, inconsistent totals, prompt injection, refunds and unfamiliar expense types.
3. **Model:** complete a compatible hardware training run. Preserve model revision, package versions, parameters and logs. Verify artifacts load after export and quantization.
4. **Evaluation:** run baseline and trained model under the same conditions. Use independently held-out examples and fact-level annotations; report counts, per-domain results, failures and uncertainty. Do not equate eight keyword/schema checks with accounting accuracy.
5. **Rechly:** test the actual application integration, human approval, error handling, authentication and data retention in its own repository/deployment. This local demo is not a production service.
6. **Publication:** owner confirms code/data licensing and model redistribution terms. Complete the model card and include checksums. Publish only measured claims and anonymized examples.

## Current evidence

CPU tests cover validation, split reproducibility, resume/retry behavior, report failure semantics, decimal totals and HTTP demo success/error handling with controlled inference responses. They do not establish live model quality. CI configuration exists; a remote Actions run and GPU training remain unverified.
