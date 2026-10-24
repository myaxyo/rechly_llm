"""
Unit tests for Rechly CLI.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_cli_cmd(args):
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "cli.py")] + args
    return subprocess.run(cmd, capture_output=True, text=True)


def test_cli_help():
    res = run_cli_cmd(["--help"])
    assert res.returncode == 0
    assert "rechly-cli" in res.stdout
    assert "invoice" in res.stdout
    assert "enhance" in res.stdout
    assert "tax" in res.stdout
    assert "dunning" in res.stdout
    assert "expense" in res.stdout


def test_cli_status():
    res = run_cli_cmd(["status"])
    assert res.returncode == 0
    assert "Rechly-DE-3B: System & Modell Status" in res.stdout
    assert "DSGVO Konformität" in res.stdout
