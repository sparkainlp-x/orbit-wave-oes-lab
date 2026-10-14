import importlib.util
import json

import pytest

from orbit_wave_oes_lab.pipeline import run_demo

pytestmark = pytest.mark.skipif(importlib.util.find_spec("oes_resilience") is None, reason="optional upstream OES-Resilience not installed")


def test_official_oes_replay_and_passport(tmp_path):
    result = run_demo(tmp_path / "oes-run", seed=20261011, steps=80, with_oes=True)
    summary = json.loads((tmp_path / "oes-run" / "run_summary.json").read_text())
    passport = json.loads((tmp_path / "oes-run" / "evidence-passport" / "synthetic-orbit-wave-demo.normalized.json").read_text())
    metadata = json.loads((tmp_path / "oes-run" / "oes-results" / "synthetic_orbit_wave_run_metadata.json").read_text())
    assert result["oes"]["upstream_version"] == "0.6.0"
    assert summary["oes_replay"]["status"] == "completed_by_upstream_oes_resilience"
    for regimes in summary["oes_replay"]["metrics_by_detector_and_regime"].values():
        for metrics in regimes.values():
            assert metrics["event_count"] == 2
            assert metrics["detected_event_count"] == 2
            assert metrics["false_positive_frame_rate"] >= 0.0
    assert passport["evidence_class"] == "synthetic"
    assert passport["integrity"]["bundle_consistent"] is True
    assert all(not argument.startswith("/") for argument in metadata["argv"] if argument.endswith((".jsonl", ".json")) or argument == "oes-results")
    assert str(tmp_path) not in json.dumps(metadata)
