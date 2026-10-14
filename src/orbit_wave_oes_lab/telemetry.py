"""Synthetic telemetry frame writer and optional official OES replay adapter."""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import subprocess
import sys
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
from typing import Any

CHANNELS = 512
BLOCK_SIZE = 32
BLOCKS = CHANNELS // BLOCK_SIZE


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frame(timestamp: datetime, values: list[float], *, event_label: str = "none", event_id: str | None = None, affected_blocks: Sequence[int] = ()) -> dict[str, Any]:
    return {
        "timestamp": timestamp.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "channels": values,
        "regime": "synthetic_orbit_demo",
        "event_label": event_label,
        "event_id": event_id,
        "affected_blocks": list(affected_blocks),
    }


def generate_replays(
    timeline: Sequence[dict[str, Any]],
    *,
    seed: int = 20261011,
    calibration_frames: int = 80,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return event-free calibration and labeled held-out OES replay records.

    The 512 values are purpose-built synthetic telemetry numbers. They are not
    mapped to physical spacecraft sensors or quantum hardware observables.
    """
    if len(timeline) < 18:
        raise ValueError("timeline must contain at least 18 rows")
    if isinstance(calibration_frames, bool) or not isinstance(calibration_frames, int) or calibration_frames < 10:
        raise ValueError("calibration_frames must be an integer >= 10")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    start = datetime.fromisoformat(str(timeline[0]["timestamp_utc"]).replace("Z", "+00:00")).astimezone(timezone.utc)
    cadence = 60
    rng_cal, rng_eval = random.Random(seed + 1), random.Random(seed + 2)  # noqa: S311 - deterministic synthetic telemetry only; never used for secrets.
    calibration: list[dict[str, Any]] = []
    for index in range(calibration_frames):
        phase = 2.0 * math.pi * (index % 40) / 40.0
        values = [0.025 * math.sin(phase + channel * 0.013) + rng_cal.gauss(0.0, 0.045) for channel in range(CHANNELS)]
        calibration.append(_frame(start - timedelta(seconds=(calibration_frames - index) * cadence), values))

    evaluation: list[dict[str, Any]] = []
    eval_start = start + timedelta(seconds=cadence)
    for index, state in enumerate(timeline):
        phase = float(state["orbit_phase_rad"])
        thermal = float(state["thermal_index_arbitrary"])
        env = float(state["environment_pulse_proxy_arbitrary"])
        values = [
            0.025 * math.sin(phase + channel * 0.013)
            + 0.012 * (thermal - 0.5)
            + rng_eval.gauss(0.0, 0.045)
            for channel in range(CHANNELS)
        ]
        if 24 <= index < 27:
            for channel in range(5 * BLOCK_SIZE, 6 * BLOCK_SIZE):
                values[channel] += 0.75
            label, event_id, affected = "synthetic_local_burst", "synthetic-event-local-01", [5]
        elif 57 <= index < 59:
            values = [value + 0.55 for value in values]
            label, event_id, affected = "synthetic_common_shift", "synthetic-event-global-02", list(range(BLOCKS))
        else:
            # A small environment-dependent effect is synthetic and not a sensor mapping.
            if env > 0.5:
                values[0] += 0.03
            label, event_id, affected = "none", None, []
        stamp = eval_start + timedelta(seconds=index * cadence)
        evaluation.append(_frame(stamp, values, event_label=label, event_id=event_id, affected_blocks=affected))
    return calibration, evaluation


def write_jsonl(path: str | Path, frames: Sequence[dict[str, Any]]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(frame, separators=(",", ":"), allow_nan=False) + "\n" for frame in frames)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def make_preregistration(calibration_path: str | Path) -> dict[str, Any]:
    """Create a schema-2 replay protocol with current UTC time and calibration hash."""
    calibration_path = Path(calibration_path)
    return {
        "schema_version": 2,
        "protocol_id": "orbit-wave-oes-synthetic-demo-v1",
        "locked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "detectors": ["oes32", "maxabs"],
        "warmup": 8,
        "threshold_policy": {
            "mode": "calibrated",
            "target_fp": 0.05,
            "unit": "frame",
            "calibration_sha256": _sha256(calibration_path),
        },
        "score_spec": {
            "channel_count": CHANNELS,
            "block_size": BLOCK_SIZE,
            "weights": {"peak_abs": 0.45, "rms": 0.35, "mean_abs": 0.20},
            "comparison": ">=",
        },
        "event_hit_rule": "any_alert_frame_during_event",
        "localization_rule": "framewise_micro_precision_recall_iou",
        "latency_rule": "first_alert_frame_minus_first_event_frame_ms",
    }


def write_preregistration(path: str | Path, calibration_path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(make_preregistration(calibration_path), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_official_oes(
    *, input_path: str | Path, calibration_path: str | Path, prereg_path: str | Path,
    out_dir: str | Path, prefix: str = "orbit_wave_oes", quiet: bool = True,
) -> dict[str, Any]:
    """Delegate scoring to the installed upstream `oes_resilience` command."""
    try:
        oes_resilience = import_module("oes_resilience")
    except ImportError as exc:
        raise RuntimeError("OES not installed; install the optional project extra or upstream OES-Resilience v0.6.0") from exc
    installed_version = getattr(oes_resilience, "__version__", None)
    if installed_version != "0.6.0":
        raise RuntimeError(f"OES replay requires upstream OES-Resilience v0.6.0; found {installed_version!r}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved = [Path(input_path).resolve(), Path(calibration_path).resolve(), Path(prereg_path).resolve(), out_dir.resolve()]
    working_dir = Path(os.path.commonpath([str(path) for path in resolved]))
    relative = [path.relative_to(working_dir).as_posix() for path in resolved]
    command = [
        sys.executable, "-m", "oes_resilience", "replay",
        "--input", relative[0],
        "--calibration", relative[1],
        "--prereg", relative[2],
        "--out-dir", relative[3],
        "--prefix", prefix,
        "--verify",
    ]
    if quiet:
        command.append("--quiet")
    # The executable is sys.executable, the module name is fixed, arguments are a list, and shell execution is disabled.
    result = subprocess.run(command, cwd=working_dir, text=True, capture_output=True, check=False, shell=False)  # noqa: S603
    if result.returncode:
        raise RuntimeError(
            f"upstream OES-Resilience replay failed (exit {result.returncode})\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    report = out_dir / f"{prefix}_report.json"
    scorecard = out_dir / f"{prefix}_scorecard.csv"
    if not report.is_file() or not scorecard.is_file():
        raise RuntimeError("upstream OES-Resilience returned success but expected report artifacts are missing")
    try:
        report_data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read upstream OES report: {exc}") from exc
    metrics_by_detector: dict[str, dict[str, dict[str, Any]]] = {}
    for detector_name, detector_data in report_data.get("detectors", {}).items():
        metrics_by_detector[detector_name] = {}
        for regime, values in detector_data.get("regimes", {}).items():
            metrics_by_detector[detector_name][regime] = {
                key: values.get(key)
                for key in (
                    "event_count", "detected_event_count", "event_recall",
                    "false_positive_frame_count", "false_positive_frame_rate",
                    "localization", "detection_latency_ms",
                )
                if key in values
            }
            localization = values.get("block_localization")
            if isinstance(localization, dict):
                metrics_by_detector[detector_name][regime]["localization_iou"] = localization.get("iou")
    if not metrics_by_detector:
        raise RuntimeError("upstream OES report contains no detector metrics")
    return {
        "status": "completed_by_upstream_oes_resilience",
        "upstream_repository": "https://github.com/sparkainlp-x/oes-resilience",
        "upstream_version": installed_version,
        "report_path": str(report),
        "scorecard_path": str(scorecard),
        "metrics_by_detector_and_regime": metrics_by_detector,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
    }
