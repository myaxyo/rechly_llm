# Contributing

Use Python 3.11 or 3.12. Create a virtual environment and install `requirements.txt` with `-c constraints.txt`. Run `python -m pytest -q` and `python scripts/validate_dataset.py data/seed_dataset.jsonl` before proposing a change.

Include regression tests for behavior changes. Keep credentials and customer documents out of examples and logs. Keep generated datasets, checkpoints and local evaluation outputs in ignored paths. For benchmark contributions, include hardware, model digest, parameters and reproducible commands, and clearly label simulated responses.

German accounting contributions are especially valuable when they document ambiguity, official source dates and expert review. Format validation must not be presented as legal certification. Discuss licensing and provenance with the repository owner before contributing datasets or distributing weights.
