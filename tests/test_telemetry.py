import hashlib
import json

from orbit_wave_oes_lab.orbit import OrbitConfig, generate_timeline
from orbit_wave_oes_lab.telemetry import (
    BLOCKS,
    CHANNELS,
    generate_replays,
    write_jsonl,
    write_preregistration,
)


def test_replay_has_valid_shape_and_separate_clean_calibration(tmp_path):
    timeline = generate_timeline(OrbitConfig(steps=80))
    calibration, evaluation = generate_replays(timeline, seed=17, calibration_frames=24)
    assert len(calibration) == 24
    assert all(len(frame["channels"]) == CHANNELS for frame in calibration + evaluation)
    assert all(frame["event_label"] == "none" for frame in calibration)
    assert all(frame["event_id"] is None and frame["affected_blocks"] == [] for frame in calibration)
    event_frames = [frame for frame in evaluation if frame["event_label"] != "none"]
    assert [frame["event_label"] for frame in event_frames[:3]] == ["synthetic_local_burst"] * 3
    assert event_frames[0]["affected_blocks"] == [5]
    assert event_frames[-1]["affected_blocks"] == list(range(BLOCKS))
    assert all(isinstance(value, float) for frame in evaluation for value in frame["channels"])

    calibration_path = write_jsonl(tmp_path / "calibration.jsonl", calibration)
    protocol_path = write_preregistration(tmp_path / "protocol.json", calibration_path)
    protocol = json.loads(protocol_path.read_text())
    assert protocol["threshold_policy"]["calibration_sha256"] == hashlib.sha256(calibration_path.read_bytes()).hexdigest()
    assert protocol["score_spec"]["channel_count"] == CHANNELS
