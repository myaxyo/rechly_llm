# Rechly research design

The target is a small German accounting assistant for local inference in Rechly. The initial candidate is Qwen2.5-3B-Instruct, with optional LoRA fine-tuning and GGUF quantization. This is a research choice, not a measured winner.

The pipeline is: reviewed ShareGPT data → validated independent splits → baseline evaluation → training → export → equivalent evaluation → human review → versioned release. See [training](docs/TRAINING.md) and [release criteria](docs/RELEASE.md).

Scope includes invoice extraction, professional line-item wording, tax-clause suggestions, dunning drafts and expense categorization. The model proposes drafts; the application and user remain responsible for business facts and tax decisions. Do not train on identifiable customer invoices without an appropriate authorized data process.

Record hardware, memory, runtime, model revision, dataset hashes, inference parameters and failure examples for every experiment. Claims about tokens per second, memory footprint, training time or legal correctness require evidence. Neither local execution nor quantization establishes compliance.
