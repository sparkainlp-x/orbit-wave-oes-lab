import json

from orbit_wave_oes_lab.pipeline import run_demo


def test_demo_builds_passport_and_marks_analog_capture_missing(tmp_path):
    result = run_demo(tmp_path / "run", seed=20261011, steps=40, with_oes=False)
    assert result["status"] == "completed"
    assert result["evidence_class"] == "SYNTHETIC"
    assert (tmp_path / "run" / "orbit_payload_timeline.csv").is_file()
    assert (tmp_path / "run" / "binaural_calibration_reference.wav").is_file()
    assert not (tmp_path / "run" / "capture.wav").exists()
    assert (tmp_path / "run" / "evidence-passport" / "synthetic-orbit-wave-demo.html").is_file()
    passport = json.loads((tmp_path / "run" / "evidence-passport" / "synthetic-orbit-wave-demo.normalized.json").read_text())
    assert passport["evidence_class"] == "synthetic"
    assert passport["integrity"]["bundle_consistent"] is True
    assert len(passport["integrity"]["files"]) == 8
    assert "not authenticated" in " ".join(passport["limitations"]).lower() or "not authenticated" in " ".join(result["limitations"]).lower()
