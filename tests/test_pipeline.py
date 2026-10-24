import copy
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import generate_dataset as generator
import evaluate_model as evaluation
from validate_dataset import validate_sharegpt_record, validate_file
from prepare_dataset import split_dataset

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / 'data/seed_dataset.jsonl'
RECORDS = [json.loads(line) for line in SEEDS.read_text().splitlines()]

@pytest.mark.parametrize('record', RECORDS)
def test_seeds(record):
    assert validate_sharegpt_record(record, 1)[0]

@pytest.mark.parametrize('record', [None, [], {}, {'conversations': None},
    {'conversations': [None, {}]}, {'conversations': [{'value': 3}, {'value': []}]},
    {'conversations': [{'from': 'human', 'value': 'a'}, {'from': 'gpt', 'value': 'b'}, {}]}])
def test_malformed_records(record):
    assert not validate_sharegpt_record(record, 1)[0]

def test_empty_and_duplicate_files(tmp_path):
    file = tmp_path / 'data.jsonl'
    file.write_text('')
    assert not validate_file(file)
    file.write_text((json.dumps(RECORDS[0]) + '\n') * 2)
    assert not validate_file(file)

def test_splits_reproducible_and_disjoint(tmp_path):
    a = split_dataset(SEEDS, tmp_path / 'a')
    b = split_dataset(SEEDS, tmp_path / 'b')
    assert a == b
    sets = [set((tmp_path / 'a' / (s + '.jsonl')).read_text().splitlines()) for s in ('train', 'valid', 'test')]
    assert all(sets)
    assert not sets[0] & sets[1] and not sets[0] & sets[2] and not sets[1] & sets[2]
    assert sum(map(len, sets)) == 25
    with pytest.raises(FileExistsError):
        split_dataset(SEEDS, tmp_path / 'a')

def test_resume_all_domains():
    counts = generator.count_existing_domain_samples(SEEDS)
    assert sum(counts.values()) == 25
    assert all(counts.values())

def args(tmp_path, **kwargs):
    values = dict(provider='ollama', model='test', output=str(tmp_path / 'output.jsonl'),
                  domain='text_to_invoice', count=1, batch_size=1, max_attempts=2, base_url=None)
    values.update(kwargs)
    return SimpleNamespace(**values)

def test_generator_caps_and_resumes(tmp_path, monkeypatch):
    calls = []
    def query(**kwargs):
        calls.append(kwargs)
        return '\n'.join(json.dumps(r) for r in RECORDS[:3])
    monkeypatch.setattr(generator, 'query_llm', query)
    monkeypatch.setattr(generator.time, 'sleep', lambda _: None)
    config = args(tmp_path)
    generator.run_generation(config)
    assert len(Path(config.output).read_text().splitlines()) == 1
    generator.run_generation(config)
    assert len(calls) == 1

@pytest.mark.parametrize('response', ['not json', json.dumps(RECORDS[-1])])
def test_generator_stops_without_progress(tmp_path, monkeypatch, response):
    monkeypatch.setattr(generator, 'query_llm', lambda **_: response)
    monkeypatch.setattr(generator.time, 'sleep', lambda _: None)
    with pytest.raises(RuntimeError, match='No progress'):
        generator.run_generation(args(tmp_path))

def test_generator_missing_key(tmp_path, monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    with pytest.raises(ValueError, match='ANTHROPIC_API_KEY'):
        generator.run_generation(args(tmp_path, provider='anthropic'))

@pytest.mark.parametrize('response', ['{}', '[]', 'null', '```json\n{}\n```',
    '{"client_name":"X","due_days":14,"items":[]}'])
def test_eval_rejects_invalid_invoice(response):
    assert evaluation.score_response(evaluation.TEST_CASES[0], response)

def test_eval_reports_transport_errors(monkeypatch):
    def fail(*_):
        raise ConnectionError('private transport details')
    monkeypatch.setattr(evaluation, 'query_model', fail)
    report = evaluation.evaluate('unavailable', 'http://localhost')
    assert report['errors'] == 8 and report['passed'] == 0
    assert 'private transport' not in json.dumps(report)

def test_eval_exit_status(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluation, 'evaluate', lambda *_: {'passed': 0, 'total': 8})
    monkeypatch.setattr('sys.argv', ['evaluate_model.py', '--report', str(tmp_path / 'report.json')])
    assert evaluation.main() == 1
    assert json.loads((tmp_path / 'report.json').read_text())['passed'] == 0

@pytest.mark.parametrize('value', ['{"price": NaN}', '{"price": Infinity}', '{"price": 1e999}', '{"price":1,"price":2}'])
def test_strict_json(value):
    from json_utils import loads
    with pytest.raises(ValueError):
        loads(value)

def test_evaluation_valid_invoice_and_wrong_facts():
    case = evaluation.TEST_CASES[0]
    invoice = {'client_name': 'Kanzlei Schmidt & Partner', 'due_days': 14,
               'items': [{'description': 'IT-Forensik', 'quantity': 12, 'unit_of_measure': 'Stunde', 'price': 140, 'tax_rate_percent': 19},
                         {'description': 'Anfahrt', 'quantity': 1, 'unit_of_measure': 'Pauschal', 'price': 80, 'tax_rate_percent': 19}]}
    assert evaluation.score_response(case, json.dumps(invoice)) == []
    invoice['items'][0]['price'] = 999
    assert evaluation.score_response(case, json.dumps(invoice))

def test_mlx_conversion_disjoint(tmp_path):
    from train_mlx import prepare_mlx_data
    prepare_mlx_data(SEEDS, tmp_path)
    splits = [list(map(json.loads, (tmp_path / f'{name}.jsonl').read_text().splitlines())) for name in ('train','valid','test')]
    assert [len(records) for records in splits] == [15, 5, 5]
    assert splits[0][0]['messages'][0]['role'] == 'user'
    assert splits[0][0]['messages'][1]['role'] == 'assistant'
    with pytest.raises(FileExistsError):
        prepare_mlx_data(SEEDS, tmp_path)
