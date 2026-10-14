"""Offline stereo calibration stimulus and user-capture analysis.

This module never opens, records from, or plays to an audio device. A WAV capture
is user supplied and is not authenticated as an analog measurement.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import wave
from pathlib import Path
from typing import Any

FREQUENCIES_HZ = (125, 250, 500, 1000, 2000, 4000, 8000)
PROTOCOL_VERSION = "1"
MAX_CAPTURE_SECONDS = 600


class AudioCalibrationError(ValueError):
    """Invalid reference/capture WAV or calibration protocol."""


def _protocol_path(reference_path: Path) -> Path:
    return reference_path.with_suffix(reference_path.suffix + ".json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_reference_wav(
    path: str | Path,
    *,
    sample_rate_hz: int = 48_000,
    tone_level: float = 0.25,
    tone_duration_s: float = 0.4,
    gap_duration_s: float = 0.1,
    frequencies_hz: tuple[int, ...] = FREQUENCIES_HZ,
) -> dict[str, Any]:
    """Write a 16-bit PCM stereo stepped-tone reference and JSON sidecar.

    For every frequency, a left-only segment is followed by a right-only
    segment. The sequence is a stimulus for external test equipment, not a
    calibration result.
    """
    path = Path(path)
    if isinstance(sample_rate_hz, bool) or not isinstance(sample_rate_hz, int) or sample_rate_hz < 16_000:
        raise AudioCalibrationError("sample_rate_hz must be an integer >= 16000")
    if not math.isfinite(tone_level) or not 0.01 <= tone_level <= 0.8:
        raise AudioCalibrationError("tone_level must be between 0.01 and 0.8 full scale")
    if not math.isfinite(tone_duration_s) or tone_duration_s < 0.2:
        raise AudioCalibrationError("tone_duration_s must be at least 0.2 seconds")
    if not math.isfinite(gap_duration_s) or gap_duration_s < 0.02:
        raise AudioCalibrationError("gap_duration_s must be at least 0.02 seconds")
    if not frequencies_hz or any(isinstance(f, bool) or not isinstance(f, int) or f <= 0 or f >= sample_rate_hz / 2 for f in frequencies_hz):
        raise AudioCalibrationError("all test frequencies must be positive integers below Nyquist")

    tone_frames = round(tone_duration_s * sample_rate_hz)
    gap_frames = round(gap_duration_s * sample_rate_hz)
    preamble_frames = round(0.25 * sample_rate_hz)
    ramp_frames = max(1, min(round(0.01 * sample_rate_hz), tone_frames // 10))
    stereo: list[tuple[float, float]] = [(0.0, 0.0)] * preamble_frames
    segments: list[dict[str, Any]] = []
    for frequency in frequencies_hz:
        for stimulus_channel in (0, 1):
            start = len(stereo)
            for sample_index in range(tone_frames):
                edge = min(1.0, (sample_index + 1) / ramp_frames, (tone_frames - sample_index) / ramp_frames)
                value = tone_level * edge * math.sin(2.0 * math.pi * frequency * sample_index / sample_rate_hz)
                stereo.append((value, 0.0) if stimulus_channel == 0 else (0.0, value))
            end = len(stereo)
            segments.append({
                "frequency_hz": frequency,
                "stimulus_channel": stimulus_channel,
                "start_sample": start,
                "end_sample": end,
                "tone_level_full_scale": tone_level,
            })
            stereo.extend([(0.0, 0.0)] * gap_frames)

    path.parent.mkdir(parents=True, exist_ok=True)
    packed = bytearray()
    for left, right in stereo:
        lval = max(-32768, min(32767, round(left * 32767)))
        rval = max(-32768, min(32767, round(right * 32767)))
        packed.extend(struct.pack("<hh", lval, rval))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(sample_rate_hz)
        output.writeframes(packed)

    protocol: dict[str, Any] = {
        "schema": "orbit-wave-oes/binaural-calibration-reference/1",
        "protocol_version": PROTOCOL_VERSION,
        "sample_rate_hz": sample_rate_hz,
        "channels": ["left stimulus", "right stimulus"],
        "sample_format": "PCM signed 16-bit little-endian",
        "tone_duration_seconds": tone_duration_s,
        "gap_duration_seconds": gap_duration_s,
        "preamble_duration_seconds": 0.25,
        "segments": segments,
        "reference_wav_sha256": _sha256(path),
        "warning": "Generated digital stimulus only; not an analog calibration or acoustic level reference.",
    }
    sidecar = _protocol_path(path)
    sidecar.write_text(json.dumps(protocol, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return protocol


def _read_pcm_stereo(
    path: Path, *, max_seconds: float | None = None,
) -> tuple[int, list[tuple[float, float]], int]:
    try:
        with wave.open(str(path), "rb") as source:
            channels = source.getnchannels()
            width = source.getsampwidth()
            sample_rate = source.getframerate()
            frame_count = source.getnframes()
            compression = source.getcomptype()
            if max_seconds is not None and sample_rate > 0 and frame_count / sample_rate > max_seconds:
                raise AudioCalibrationError(
                    f"{path} is {frame_count / sample_rate:.1f} s long; captures longer than "
                    f"{max_seconds:g} s ({max_seconds / 60:g} minutes) are rejected"
                )
            raw = source.readframes(frame_count)
    except (OSError, EOFError, wave.Error) as exc:
        raise AudioCalibrationError(f"cannot read WAV {path}: {exc}") from exc
    if channels != 2:
        raise AudioCalibrationError(f"{path} must be stereo/two-channel; received {channels} channel(s)")
    if compression != "NONE":
        raise AudioCalibrationError(f"{path} must be uncompressed PCM WAV")
    if width not in (1, 2, 3, 4):
        raise AudioCalibrationError(f"unsupported PCM sample width {width} bytes")
    samples: list[tuple[float, float]] = []
    if width == 1:
        for left, right in struct.iter_unpack("<BB", raw):
            samples.append(((left - 128) / 128.0, (right - 128) / 128.0))
    elif width == 2:
        for left, right in struct.iter_unpack("<hh", raw):
            samples.append((left / 32768.0, right / 32768.0))
    elif width == 3:
        for offset in range(0, len(raw), 6):
            left = int.from_bytes(raw[offset:offset + 3], "little", signed=True)
            right = int.from_bytes(raw[offset + 3:offset + 6], "little", signed=True)
            samples.append((left / 8388608.0, right / 8388608.0))
    else:
        for left, right in struct.iter_unpack("<ii", raw):
            samples.append((left / 2147483648.0, right / 2147483648.0))
    if len(samples) != frame_count:
        raise AudioCalibrationError(f"truncated PCM data in {path}")
    return sample_rate, samples, width


def _is_clipped(value: float, width: int) -> bool:
    """Return True at either PCM rail for the given sample width in bytes.

    Signed n-bit PCM decodes to [-1, (2**(n-1) - 1) / 2**(n-1)]; 8-bit positive
    full scale is 127/128 = 0.9921875, so a fixed 0.999 threshold would miss it.
    """
    full_scale = 2 ** (8 * width - 1)
    return value >= (full_scale - 1) / full_scale or value <= -1.0


def _tone_component(
    samples: list[tuple[float, float]], *, channel: int, start: int, end: int,
    frequency_hz: float, sample_rate_hz: int,
) -> complex:
    length = end - start
    if length <= 0:
        raise AudioCalibrationError("empty tone segment in protocol")
    real = imag = 0.0
    for n, frame in enumerate(samples[start:end]):
        angle = 2.0 * math.pi * frequency_hz * n / sample_rate_hz
        value = frame[channel]
        real += value * math.cos(angle)
        imag -= value * math.sin(angle)
    scale = 2.0 / length
    return complex(real * scale, imag * scale)


def _wrap_phase(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def analyze_capture(
    reference_path: str | Path,
    capture_path: str | Path,
    *,
    capture_offset_samples: int = 0,
) -> dict[str, Any]:
    """Compare a recorded two-channel PCM WAV with this tool's reference stimulus.

    The reported gains are relative digital sample ratios. This routine cannot
    convert them to voltage, SPL, transducer sensitivity, or traceable calibration.
    """
    reference_path, capture_path = Path(reference_path), Path(capture_path)
    if isinstance(capture_offset_samples, bool) or not isinstance(capture_offset_samples, int) or capture_offset_samples < 0:
        raise AudioCalibrationError("capture_offset_samples must be a non-negative integer")
    sidecar = _protocol_path(reference_path)
    try:
        protocol = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AudioCalibrationError(f"cannot read reference protocol sidecar {sidecar}: {exc}") from exc
    if protocol.get("schema") != "orbit-wave-oes/binaural-calibration-reference/1":
        raise AudioCalibrationError("unrecognized reference protocol schema")
    expected_hash = protocol.get("reference_wav_sha256")
    actual_hash = _sha256(reference_path)
    if expected_hash != actual_hash:
        raise AudioCalibrationError("reference WAV SHA-256 does not match its protocol sidecar")

    ref_rate, ref_samples, ref_width = _read_pcm_stereo(reference_path)
    cap_rate, cap_samples, cap_width = _read_pcm_stereo(capture_path, max_seconds=MAX_CAPTURE_SECONDS)
    if ref_rate != protocol.get("sample_rate_hz"):
        raise AudioCalibrationError("reference WAV sample rate does not match its protocol")
    if cap_rate != ref_rate:
        raise AudioCalibrationError(f"capture sample rate {cap_rate} differs from reference {ref_rate}")
    if capture_offset_samples + len(ref_samples) > len(cap_samples):
        raise AudioCalibrationError("capture is too short for reference duration plus the declared offset")

    transfer_rows: list[dict[str, Any]] = []
    for segment in protocol["segments"]:
        frequency = int(segment["frequency_hz"])
        stimulus = int(segment["stimulus_channel"])
        start, end = int(segment["start_sample"]), int(segment["end_sample"])
        ref_component = _tone_component(
            ref_samples, channel=stimulus, start=start, end=end,
            frequency_hz=frequency, sample_rate_hz=ref_rate,
        )
        if abs(ref_component) <= 1e-12:
            raise AudioCalibrationError(f"reference tone at {frequency} Hz is numerically zero")
        capture_start, capture_end = start + capture_offset_samples, end + capture_offset_samples
        components = [
            _tone_component(
                cap_samples, channel=channel, start=capture_start, end=capture_end,
                frequency_hz=frequency, sample_rate_hz=cap_rate,
            )
            for channel in (0, 1)
        ]
        magnitudes = [abs(value) for value in components]
        gains = [magnitude / abs(ref_component) for magnitude in magnitudes]
        phases = [_wrap_phase(math.atan2(value.imag, value.real) - math.atan2(ref_component.imag, ref_component.real)) for value in components]
        direct = gains[stimulus]
        leakage_channel = 1 - stimulus
        leakage_ratio = gains[leakage_channel] / direct if direct > 1e-15 else None
        leakage_db = 20.0 * math.log10(leakage_ratio) if leakage_ratio is not None and leakage_ratio > 0 else None
        direct_gain_db = 20.0 * math.log10(direct) if direct > 0 else None
        transfer_rows.append({
            "frequency_hz": frequency,
            "stimulus_channel": "left" if stimulus == 0 else "right",
            "capture_left_gain_ratio": gains[0],
            "capture_right_gain_ratio": gains[1],
            "direct_gain_ratio": direct,
            "direct_gain_db_relative_to_digital_reference": direct_gain_db,
            "capture_left_phase_difference_rad": phases[0],
            "capture_right_phase_difference_rad": phases[1],
            "direct_phase_difference_rad": phases[stimulus],
            "leakage_channel": "right" if stimulus == 0 else "left",
            "leakage_to_direct_ratio": leakage_ratio,
            "leakage_db_relative_to_direct": leakage_db,
            "inter_channel_gain_difference_db_left_minus_right": (
                20.0 * math.log10(gains[0] / gains[1]) if gains[0] > 0 and gains[1] > 0 else None
            ),
            "phase_equivalent_left_right_delay_ms_wrapped": (
                1000.0 * _wrap_phase(phases[0] - phases[1]) / (2.0 * math.pi * frequency)
            ),
        })

    clipped = sum(_is_clipped(value, cap_width) for frame in cap_samples for value in frame)
    sample_count = 2 * len(cap_samples)
    peak = max((abs(value) for frame in cap_samples for value in frame), default=0.0)
    return {
        "schema": "orbit-wave-oes/binaural-capture-analysis/1",
        "evidence_class": "USER_PROVIDED_CAPTURE_NOT_AUTHENTICATED",
        "reference_wav_sha256": actual_hash,
        "capture_wav_sha256": _sha256(capture_path),
        "sample_rate_hz": cap_rate,
        "reference_pcm_width_bytes": ref_width,
        "capture_pcm_width_bytes": cap_width,
        "capture_offset_samples": capture_offset_samples,
        "capture_duration_seconds": len(cap_samples) / cap_rate,
        "capture_peak_full_scale": peak,
        "capture_clipped_sample_fraction": clipped / sample_count if sample_count else 0.0,
        "frequency_response": transfer_rows,
        "units_and_scope": {
            "gain": "relative digital sample ratio and dB; not volts or SPL",
            "phase": "phase difference relative to the reference WAV under the declared sample offset",
            "delay": "wrapped phase-equivalent left/right delay; not an unambiguous broadband group delay",
            "hardware_calibration_claimed": False,
            "audio_device_opened_or_played": False,
        },
        "limitations": [
            "The analyzer cannot authenticate that the capture was made through an analog or acoustic path.",
            "No calibrated microphone, coupler, voltage standard, DAC/ADC, or transducer sensitivity is assumed.",
            "Absolute SPL/voltage, traceability, room response, and physical placement are not inferred.",
            "Relative frequency response, phase, leakage and clipping describe only the supplied WAV and its declared alignment.",
            "No correction equalizer or hardware setting is applied.",
        ],
    }
