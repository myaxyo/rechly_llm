# Ownership and data provenance

The owner has confirmed that the project code is theirs. They have also stated that rights to the existing seed data still need checking. A specific code license has not yet been confirmed, so no new license grant is added by this handoff.

| Asset | Current evidence | Next action |
| --- | --- | --- |
| Original project code | Ownership confirmed by the project owner | Owner selects the public code license before release |
| `data/seed_dataset.jsonl` (25 pairs) | Usage and redistribution rights unresolved | Establish origin and permitted uses for each example, or replace with rights-cleared examples |
| Generated datasets | Depends on source inputs and generator terms | Record generator/version, date, allowed use, review and source rights |
| Qwen / MLX base weights | Third-party assets, not bundled here | Verify the exact model revision, license and redistribution obligations |
| Future adapters / GGUF | Not trained in this environment | Record all contributing data/model rights before publication |

Use a record per data source or example with: identifier/hash, author/source, creation date, permission/license, permitted training use, permitted redistribution, reviewer/date and official factual references. “Publicly accessible” and “synthetically generated” do not by themselves establish all necessary rights.

Do not describe the current seed dataset or derived weights as Apache-2.0 licensed until the rights are established. Keep provenance records with experiment manifests. Local format checks are not a licensing assessment.
