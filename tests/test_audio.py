import json
import struct
import wave

import pytest

from orbit_wave_oes_lab.audio import (
    AudioCalibrationError,
    analyze_capture,
    write_reference_wav,
)


def test_identity_capture_is_reported_as_unverified_user_wav(tmp_path):
    reference = tmp_path / "reference.wav"
    protocol = write_reference_wav(reference, sample_rate_hz=32_000)
    report = analyze_capture(reference, reference)
    assert protocol["reference_wav_sha256"] == report["reference_wav_sha256"]
    assert report["evidence_class"] == "USER_PROVIDED_CAPTURE_NOT_AUTHENTICATED"
    assert report["units_and_scope"]["hardware_calibration_claimed"] is False
    assert report["units_and_scope"]["audio_device_opened_or_played"] is False
    assert len(report["frequency_response"]) == 14
    for row in report["frequency_response"]:
        assert row["direct_gain_db_relative_to_digital_reference"] == pytest.approx(0.0, abs=0.02)
        assert row["leakage_to_direct_ratio"] == pytest.approx(0.0, abs=1e-12)


def test_capture_offset_is_supported(tmp_path):
    reference = tmp_path / "reference.wav"
    capture = tmp_path / "capture.wav"
    write_reference_wav(reference, sample_rate_hz=32_000)
    offset = 256
    with wave.open(str(reference), "rb") as src:
        raw = src.readframes(src.getnframes())
    with wave.open(str(capture), "wb") as dst:
        dst.setnchannels(2)
        dst.setsampwidth(2)
        dst.setframerate(32_000)
        dst.writeframes(b"\x00" * offset * 4 + raw)
    report = analyze_capture(reference, capture, capture_offset_samples=offset)
    assert report["capture_offset_samples"] == offset
    assert report["frequency_response"][0]["direct_gain_db_relative_to_digital_reference"] == pytest.approx(0.0, abs=0.02)


def test_reference_hash_tampering_fails_closed(tmp_path):
    reference = tmp_path / "reference.wav"
    write_reference_wav(reference, sample_rate_hz=32_000)
    sidecar = reference.with_suffix(".wav.json")
    data = json.loads(sidecar.read_text())
    data["reference_wav_sha256"] = "0" * 64
    sidecar.write_text(json.dumps(data))
    with pytest.raises(AudioCalibrationError, match="SHA-256"):
        analyze_capture(reference, reference)


def test_synthetic_transfer_gain_and_leakage_are_recovered(tmp_path):
    reference = tmp_path / "reference.wav"
    capture = tmp_path / "synthetic-capture.wav"
    write_reference_wav(reference, sample_rate_hz=32_000)
    with wave.open(str(reference), "rb") as src:
        raw = src.readframes(src.getnframes())
    converted = bytearray()
    for left_i, right_i in struct.iter_unpack("<hh", raw):
        left, right = left_i / 32768.0, right_i / 32768.0
        captured_left = 0.80 * left + 0.02 * right
        captured_right = 0.03 * left + 0.72 * right
        converted.extend(struct.pack("<hh", round(captured_left * 32767), round(captured_right * 32767)))
    with wave.open(str(capture), "wb") as dst:
        dst.setnchannels(2)
        dst.setsampwidth(2)
        dst.setframerate(32_000)
        dst.writeframes(converted)

    report = analyze_capture(reference, capture)
    for row in report["frequency_response"]:
        if row["stimulus_channel"] == "left":
            assert row["direct_gain_ratio"] == pytest.approx(0.80, rel=0.01)
            assert row["leakage_to_direct_ratio"] == pytest.approx(0.03 / 0.80, rel=0.02)
        else:
            assert row["direct_gain_ratio"] == pytest.approx(0.72, rel=0.01)
            assert row["leakage_to_direct_ratio"] == pytest.approx(0.02 / 0.72, rel=0.02)
    assert report["units_and_scope"]["hardware_calibration_claimed"] is False
