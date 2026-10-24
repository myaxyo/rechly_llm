# Rechly-DE-3B model card — planned model

**Release status:** no fine-tuned weights or measured model-quality results are included.

**Intended base:** Qwen/Qwen2.5-3B-Instruct. Verify the exact base revision and its license before training or distribution. Base-model terms and dataset rights are separate from this repository's license.

**Intended use:** German-language accounting assistance, structured invoice drafts and business correspondence reviewed by a person. Not an autonomous bookkeeper or a substitute for tax advice.

**Implemented evaluation:** eight public smoke cases, JSON schema checks, selected extraction facts, tax/account expectations and keyword heuristics. Tests of software use controlled responses and are not model-performance results.

**Known limitations:** 25 seed examples; unverified legal accuracy and provenance; incomplete linguistic and industry coverage; heuristic domain classification; no measured generalization, fairness, hallucination or privacy results; no validated GPU training run; no verified production integration.

**Complete before release:** model and tokenizer revisions; training configuration and software versions; source-data provenance and hashes; training/validation/test sizes; hardware and runtime; base-versus-trained results; human-review methodology; known failures; applicable licenses; intended deployment boundaries; model and artifact checksums.
