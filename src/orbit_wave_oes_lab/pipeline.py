"""End-to-end deterministic demo pipeline and artifact generation."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from . import __version__
from .audio import write_reference_wav
from .orbit import OrbitConfig, generate_timeline
from .passport import build_passport
from .telemetry import (
    generate_replays,
    run_official_oes,
    write_jsonl,
    write_preregistration,
)
from .wave import DEFAULT_SEED, encode_symbol, run_threshold_experiment

REPOSITORY_URL = "https://github.com/sparkainlp-x/orbit-wave-oes-lab"


PROJECT_NAME = "orbit-wave-oes-lab"


def _run_git(git: str, cwd: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [git, *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _is_this_project(toplevel: Path) -> bool:
    try:
        text = (toplevel / "pyproject.toml").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return any(line.strip() == f'name = "{PROJECT_NAME}"' for line in text.splitlines())


def _git_commit(start: Path | None = None) -> str | None:
    """Return the checked-out commit SHA at build time, or None.

    A SHA is returned only when the enclosing git work tree is this project
    (its top-level pyproject.toml declares name = "orbit-wave-oes-lab"), so an
    install that happens to sit inside some other repository records None.
    """
    git = shutil.which("git")
    if git is None:
        return None
    cwd = start if start is not None else Path(__file__).resolve().parent
    toplevel = _run_git(git, cwd, "rev-parse", "--show-toplevel")
    if not toplevel or not _is_this_project(Path(toplevel)):
        return None
    sha = _run_git(git, cwd, "rev-parse", "HEAD")
    if not sha or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        return None
    return sha


LIMITATIONS = [
    "All orbit/environment, payload, telemetry and injected events in the bundled demo are synthetic.",
    "Orbit coordinates are normalized; the illumination window and thermal/radiation proxies are not calibrated to an actual orbit or spacecraft.",
    "Wave encoding and binary readout are classical software calculations; no quantum state, NV center, spin Hamiltonian or physical quantum effect is simulated.",
    "The optional OES run evaluates synthetic 512-value frames only; replay success does not establish field performance or detector superiority.",
    "The generated stereo reference is a digital stimulus, not a calibration result; no audio device is opened or played by this program.",
    "A user-supplied capture WAV is not authenticated as analog; digital gain ratios are not volts, SPL, microphone sensitivity or traceable calibration.",
    "SHA-256 matching proves byte consistency with this manifest only; it does not prove authorship, timing, measurement validity or provenance.",
    "The project does not test any physical device and claims no affiliation with any device maker or organization.",
]


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_timeline_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    columns = [
        "frame_index", "timestamp_utc", "orbit_phase_rad", "orbit_phase_fraction",
        "x_normalized", "y_normalized", "shadow_window", "illumination_fraction",
        "thermal_index_arbitrary", "environment_pulse_proxy_arbitrary", "evidence_class",
        "payload_actual_label", "payload_signal_arbitrary", "payload_predicted_label",
        "wave_amplitude_arbitrary", "wave_phase_rad_or_null", "wave_rms_arbitrary",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def run_demo(
    output_dir: str | Path,
    *,
    seed: int = DEFAULT_SEED,
    steps: int = 80,
    with_oes: bool = False,
) -> dict[str, Any]:
    """Run the complete local demo and write a hash-checked evidence passport."""
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    orbit = generate_timeline(OrbitConfig(steps=steps))
    readout = run_threshold_experiment(seed=seed)
    if len(readout["heldout_records"]) < steps:
        raise ValueError("held-out readout record count is smaller than orbit timeline")

    joined: list[dict[str, Any]] = []
    for state, measurement in zip(orbit, readout["heldout_records"][:steps]):
        encoded = encode_symbol(int(measurement["actual"]))
        joined.append({
            **state,
            "payload_actual_label": int(measurement["actual"]),
            "payload_signal_arbitrary": float(measurement["signal_arbitrary"]),
            "payload_predicted_label": int(measurement["predicted"]),
            "wave_amplitude_arbitrary": encoded["amplitude_arbitrary"],
            "wave_phase_rad_or_null": encoded["phase_rad"],
            "wave_rms_arbitrary": encoded["rms_arbitrary"],
        })
    timeline_path = _write_timeline_csv(output_dir / "orbit_payload_timeline.csv", joined)
    readout_path = _write_json(output_dir / "binary_readout.json", readout)

    reference_path = output_dir / "binaural_calibration_reference.wav"
    write_reference_wav(reference_path)
    reference_sidecar = reference_path.with_suffix(reference_path.suffix + ".json")

    calibration_frames, evaluation_frames = generate_replays(orbit, seed=seed)
    calibration_path = write_jsonl(output_dir / "oes_calibration.jsonl", calibration_frames)
    evaluation_path = write_jsonl(output_dir / "oes_evaluation.jsonl", evaluation_frames)
    prereg_path = write_preregistration(output_dir / "oes_protocol.json", calibration_path)
    protocol_data = json.loads(prereg_path.read_text(encoding="utf-8"))

    oes_result: dict[str, Any]
    optional_outputs: list[Path] = []
    if with_oes:
        oes_result = run_official_oes(
            input_path=evaluation_path,
            calibration_path=calibration_path,
            prereg_path=prereg_path,
            out_dir=output_dir / "oes-results",
            prefix="synthetic_orbit_wave",
        )
        oes_result["interpretation_note"] = (
            "These metrics score only the synthetic held-out replay. The configured 5% false-positive target "
            "applies to calibration data, not a guarantee on evaluation data."
        )
        optional_outputs = [
            Path(oes_result["report_path"]),
            Path(oes_result["scorecard_path"]),
            output_dir / "oes-results" / "synthetic_orbit_wave_manifest.json",
            output_dir / "oes-results" / "synthetic_orbit_wave_run_metadata.json",
        ]
        optional_outputs = [path for path in optional_outputs if path.is_file()]
    else:
        oes_result = {
            "status": "not_requested",
            "note": "Replay files and protocol are ready; install upstream OES-Resilience and rerun with --with-oes to score them.",
        }

    oes_result_for_summary = dict(oes_result)
    if with_oes:
        for path_key in ("report_path", "scorecard_path"):
            oes_result_for_summary[path_key] = Path(oes_result[path_key]).resolve().relative_to(output_dir).as_posix()

    summary = {
        "schema": "orbit-wave-oes/demo-summary/1",
        "project": "Orbit–Wave–OES Lab",
        "version": __version__,
        "evidence_class": "SYNTHETIC",
        "seed": seed,
        "orbit_timeline_frames": len(joined),
        "normalized_orbit_period_steps": 40,
        "payload_readout": {
            "frozen_threshold_arbitrary_units": readout["frozen_threshold"],
            "mean_label_0_calibration": readout["calibration_means"]["label_0"],
            "mean_label_1_calibration": readout["calibration_means"]["label_1"],
            "heldout_accuracy": readout["heldout_accuracy"],
            "confusion_matrix_actual_rows_predicted_columns": readout["confusion_matrix_actual_rows_predicted_columns"],
            "threshold_source": readout["threshold_source"],
        },
        "oes_replay": oes_result_for_summary,
        "analog_binaural_calibration": {
            "reference_wav": reference_path.name,
            "reference_protocol": reference_sidecar.name,
            "capture_status": "NOT_PROVIDED",
            "hardware_calibration_claimed": False,
            "audio_device_opened_or_played": False,
        },
        "limitations": LIMITATIONS,
    }
    summary_path = _write_json(output_dir / "run_summary.json", summary)

    artifacts: list[tuple[Path, str, str]] = [
        (timeline_path, "synthetic_timeline", "Normalized orbit and synthetic payload-readout rows."),
        (readout_path, "synthetic_calibration_and_readout", "Calibration-only threshold and independent synthetic held-out readout."),
        (reference_path, "digital_audio_reference", "Generated stereo stepped-tone WAV; not an analog calibration."),
        (reference_sidecar, "audio_protocol", "Tone frequencies, segment indices, and reference-file hash."),
        (calibration_path, "synthetic_oes_calibration", "Event-free synthetic 512-channel replay for threshold calibration."),
        (evaluation_path, "synthetic_oes_evaluation", "Held-out synthetic replay with known injected events."),
        (prereg_path, "protocol", "Replay protocol bound to the event-free synthetic calibration replay hash."),
        (summary_path, "run_summary", "Run-level result and explicit evidence boundaries."),
    ]
    for path in optional_outputs:
        artifacts.append((path, "upstream_oes_output", "Output emitted by the official OES-Resilience replay command."))

    manifest_path = output_dir / "passport-manifest.json"
    manifest = {
        "schema_version": 1,
        "run_id": "synthetic-orbit-wave-demo",
        "project": {
            "name": "Orbit–Wave–OES Lab",
            "version": __version__,
            "source_url": REPOSITORY_URL,
            "source_note": "Public repository; code.commit is the checked-out commit at build time, or null outside a git checkout.",
        },
        "evidence_class": "synthetic",
        "dataset": {
            "name": "Generated normalized orbit/payload/OES demonstration",
            "kind": "synthetic deterministic software inputs",
            "description": "No spacecraft, NV-diamond, audio-hardware, or field data is included.",
            "source_url": None,
        },
        "code": {"version": __version__, "commit": _git_commit()},
        "seed": seed,
        "protocol": {
            "name": "OES-Resilience schema-2 synthetic demo protocol",
            "version": "1",
            "sha256": _sha256(prereg_path),
            "locked_at": protocol_data["locked_at"],
            "lock_commit": None,
            "description": "Protocol timestamp is written by the local runner; it is not independently time-verified and is not an external preregistration.",
        },
        "baselines": ["frozen binary midpoint threshold", "official OES-Resilience oes32/maxabs detectors (only if requested)"],
        "results": [
            {
                "scope": "synthetic binary payload readout",
                "method": "calibration-only midpoint threshold held fixed for held-out sessions",
                "metrics": [
                    {"name": "threshold", "value": readout["frozen_threshold"], "unit": "arbitrary signal units", "note": "Generated from calibration sessions only; units are not physical."},
                    {"name": "heldout_accuracy", "value": readout["heldout_accuracy"], "unit": "fraction", "note": "Synthetic independent trials; not a hardware or mission metric."},
                    {"name": "orbit_timeline_frames", "value": len(joined), "unit": "frames"},
                    {"name": "official_oes_replay_completed", "value": 1 if with_oes else 0, "unit": "boolean indicator", "note": "Completion indicator only; inspect the raw upstream report for its separate synthetic metrics."},
                ],
            }
        ] + ([
            {
                "scope": "synthetic OES held-out replay",
                "method": "official OES-Resilience v0.6.0; per-detector metrics from upstream report",
                "metrics": [
                    {
                        "name": f"{detector}_{regime}_{metric_name}",
                        "value": metric_value,
                        "unit": ("fraction" if "rate" in metric_name or "recall" in metric_name or "iou" in metric_name else "frames"),
                        "note": "Synthetic evaluation replay only. Calibration false-positive target is not a held-out guarantee.",
                    }
                    for detector, regimes in oes_result["metrics_by_detector_and_regime"].items()
                    for regime, detector_metrics in regimes.items()
                    for metric_name, metric_value in detector_metrics.items()
                    if isinstance(metric_value, (int, float)) and not isinstance(metric_value, bool)
                ],
            }
        ] if with_oes else []),
        "result_label": "synthetic_example",
        "interpretation": "The run demonstrates deterministic software plumbing over generated data only; it establishes no physical, quantum, analog calibration, spacecraft, or mission performance.",
        "limitations": LIMITATIONS,
        "artifacts": [
            {"path": path.relative_to(output_dir).as_posix(), "role": role, "description": description, "sha256": _sha256(path)}
            for path, role, description in artifacts
        ],
    }
    _write_json(manifest_path, manifest)
    passport_dir = output_dir / "evidence-passport"
    passport_html, passport_json = build_passport(manifest_path, passport_dir)
    return {
        "status": "completed",
        "evidence_class": "SYNTHETIC",
        "output_dir": str(output_dir),
        "timeline_csv": str(timeline_path),
        "binary_readout_json": str(readout_path),
        "reference_wav": str(reference_path),
        "oes": oes_result,
        "passport_html": str(passport_html),
        "passport_json": str(passport_json),
        "limitations": LIMITATIONS,
    }
