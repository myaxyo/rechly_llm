import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
import pytest
import train_mlx as training

SEEDS = Path(__file__).resolve().parents[1] / 'data/seed_dataset.jsonl'


def options(tmp_path, **overrides):
    values = dict(data=SEEDS, data_dir=tmp_path / 'splits', adapter_path=tmp_path / 'adapters',
                  model='local-model', batch_size=1, iters=2, learning_rate=1e-4,
                  save_every=1, max_seq_length=128, steps_per_eval=1, prepare_only=False)
    values.update(overrides)
    return SimpleNamespace(**values)


def test_prepare_without_mlx(tmp_path, monkeypatch):
    monkeypatch.setattr(training, 'check_mac', lambda: pytest.fail('Must not check Metal'))
    training.run_mlx_training(options(tmp_path, prepare_only=True))
    manifest = json.loads((tmp_path / 'splits/manifest.json').read_text())
    assert manifest['counts'] == {'train': 15, 'valid': 5, 'test': 5}
    assert set(manifest['mlx_sha256']) == {'train', 'valid', 'test'}
    assert not (tmp_path / 'adapters').exists()


def test_wrong_platform_fails_before_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(training.platform, 'system', lambda: 'Linux')
    with pytest.raises(RuntimeError, match='Apple Silicon'):
        training.run_mlx_training(options(tmp_path))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('outcome', ['success', 'failure', 'missing_artifact'])
def test_training_records_actual_outcome(tmp_path, monkeypatch, outcome):
    monkeypatch.setattr(training, 'check_mac', lambda: None)
    def run(command, **kwargs):
        assert '--mask-prompt' in command and '--grad-checkpoint' in command
        assert '--test' not in command  # Never use held-out test data for model selection.
        assert kwargs['check'] is True
        if outcome == 'failure':
            raise subprocess.CalledProcessError(7, command)
        if outcome == 'success':
            (tmp_path / 'adapters/adapters.safetensors').write_bytes(b'test fixture only')
    monkeypatch.setattr(training.platform, 'platform', lambda: 'test-platform')
    monkeypatch.setattr(training.subprocess, 'run', run)
    if outcome == 'success':
        training.run_mlx_training(options(tmp_path))
    else:
        with pytest.raises((subprocess.CalledProcessError, RuntimeError)):
            training.run_mlx_training(options(tmp_path))
    report = json.loads((tmp_path / 'adapters/run.json').read_text())
    assert report['status'] == ('completed' if outcome == 'success' else 'failed')
    assert ('adapter_sha256' in report) == (outcome == 'success')


def test_refuses_existing_adapters(tmp_path, monkeypatch):
    monkeypatch.setattr(training, 'check_mac', lambda: None)
    (tmp_path / 'adapters').mkdir()
    with pytest.raises(FileExistsError):
        training.run_mlx_training(options(tmp_path))
    assert not (tmp_path / 'splits').exists()
