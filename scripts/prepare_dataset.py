#!/usr/bin/env python3
"""Validate and reproducibly stratify ShareGPT records without prompt leakage."""
import argparse
import hashlib
import json
from json_utils import loads as strict_loads
import random
from pathlib import Path
from collections import defaultdict
from validate_dataset import validate_sharegpt_record


def split_dataset(source, output, seed=3407):
    groups = defaultdict(list)
    seen = set()
    raw = Path(source).read_bytes()
    for index, line in enumerate(raw.decode('utf-8').splitlines(), 1):
        if not line.strip():
            continue
        record = strict_loads(line)
        valid, reason, domain = validate_sharegpt_record(record, index)
        if not valid:
            raise ValueError(f'Line {index}: {reason}')
        key = ' '.join(record['conversations'][0]['value'].casefold().split())
        if key in seen:
            raise ValueError(f'Duplicate prompt at line {index}')
        seen.add(key)
        groups[domain].append(record)
    if not groups:
        raise ValueError('Empty dataset')
    splits = {'train': [], 'valid': [], 'test': []}
    rng = random.Random(seed)
    for domain, records in sorted(groups.items()):
        if len(records) < 3:
            raise ValueError(f'{domain}: need at least 3 examples for independent splits')
        # Sort before shuffling so input ordering cannot change membership.
        records.sort(key=lambda r: json.dumps(r, sort_keys=True, ensure_ascii=False))
        rng.shuffle(records)
        held_out = max(1, int(len(records) * 0.1))
        splits['test'].extend(records[:held_out])
        splits['valid'].extend(records[held_out:2 * held_out])
        splits['train'].extend(records[2 * held_out:])
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = [output / (name + '.jsonl') for name in splits] + [output / 'manifest.json']
    if any(path.exists() for path in paths):
        raise FileExistsError('Output exists; use a new directory to preserve existing splits')
    manifest = {'source_sha256': hashlib.sha256(raw).hexdigest(), 'seed': seed,
                'counts': {k: len(v) for k, v in splits.items()}, 'sha256': {}}
    for name, records in splits.items():
        content = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records)
        (output / (name + '.jsonl')).write_text(content, encoding='utf-8')
        manifest['sha256'][name] = hashlib.sha256(content.encode()).hexdigest()
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=3407)
    args = parser.parse_args()
    try:
        print(json.dumps(split_dataset(args.source, args.output, args.seed), indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
