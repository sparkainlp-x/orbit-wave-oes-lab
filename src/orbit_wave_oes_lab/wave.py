"""Synthetic signed-amplitude wave mapping and frozen-threshold readout."""
from __future__ import annotations

from math import isfinite, pi, sin, sqrt
from random import Random
from statistics import mean
from typing import Any

DEFAULT_SEED = 20261011


def encode_symbol(label: int, *, samples: int = 64, cycles: int = 4) -> dict[str, Any]:
    """Map a binary software label to a dimensionless sine segment.

    Label 0 is zero amplitude; label 1 uses unit amplitude and phase pi/4.
    This is classical sampled arithmetic, not a physical wave or spin state.
    """
    if isinstance(label, bool) or label not in (0, 1):
        raise ValueError("label must be integer 0 or 1")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 4:
        raise ValueError("samples must be an integer >= 4")
    if isinstance(cycles, bool) or not isinstance(cycles, int) or cycles < 1 or 2 * cycles >= samples:
        raise ValueError("cycles must be positive and below the discrete Nyquist limit")
    amplitude = float(label)
    phase = pi / 4.0 if label == 1 else 0.0
    values = [amplitude * sin(2.0 * pi * cycles * n / samples + phase) for n in range(samples)]
    rms = sqrt(sum(value * value for value in values) / samples)
    return {
        "label": label,
        "amplitude_arbitrary": amplitude,
        "phase_rad": phase if label else None,
        "samples": values,
        "rms_arbitrary": rms,
        "scope": "classical dimensionless synthetic software waveform; no physical carrier or device is modeled",
    }


def run_threshold_experiment(
    *,
    seed: int = DEFAULT_SEED,
    noise_sd: float = 0.70,
    session_drift_sd: float = 0.35,
    calibration_sessions: int = 5,
    heldout_sessions: int = 10,
    shots_per_label: int = 100,
) -> dict[str, Any]:
    """Run the user-supplied two-level classifier with a calibration-only threshold.

    Calibration and held-out sessions are disjoint. The learned threshold is
    frozen before the held-out trials are generated and scored.
    """
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    for name, value in (("noise_sd", noise_sd), ("session_drift_sd", session_drift_sd)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and non-negative")
    for name, value in (("calibration_sessions", calibration_sessions), ("heldout_sessions", heldout_sessions), ("shots_per_label", shots_per_label)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer")

    rng = Random(seed)  # noqa: S311 - reproducible synthetic experiment only; never used for secrets.
    levels = {0: 0.0, 1: 1.0}  # arbitrary signal units, not GHz or measured phase

    # Calibration sessions only: estimate one fixed decision threshold.
    calibration: list[tuple[int, float]] = []
    for _session in range(calibration_sessions):
        drift = rng.gauss(0.0, session_drift_sd)
        shots = [
            (label, levels[label] + drift + rng.gauss(0.0, noise_sd))
            for label in (0, 1)
            for _ in range(shots_per_label)
        ]
        rng.shuffle(shots)
        calibration.extend(shots)

    mu0 = mean(signal for label, signal in calibration if label == 0)
    mu1 = mean(signal for label, signal in calibration if label == 1)
    threshold = (mu0 + mu1) / 2.0

    # Separate held-out sessions; threshold stays frozen.
    confusion = [[0, 0], [0, 0]]  # rows=actual label, columns=predicted label
    heldout_records: list[dict[str, int | float]] = []
    per_session_accuracy: list[dict[str, int | float]] = []
    for session in range(heldout_sessions):
        drift = rng.gauss(0.0, session_drift_sd)
        trials = [
            (label, levels[label] + drift + rng.gauss(0.0, noise_sd))
            for label in (0, 1)
            for _ in range(shots_per_label)
        ]
        rng.shuffle(trials)
        correct = 0
        for actual, signal in trials:
            predicted = int(signal >= threshold)
            confusion[actual][predicted] += 1
            correct += actual == predicted
            heldout_records.append({
                "session": session,
                "actual": actual,
                "signal_arbitrary": signal,
                "predicted": predicted,
            })
        accuracy = correct / len(trials)
        per_session_accuracy.append({"session": session, "accuracy": accuracy})

    return {
        "evidence_class": "SYNTHETIC",
        "seed": seed,
        "signal_units": "arbitrary; not GHz, volts, photon counts, or measured phase",
        "levels": levels,
        "noise_sd": float(noise_sd),
        "session_drift_sd": float(session_drift_sd),
        "calibration_sessions": calibration_sessions,
        "heldout_sessions": heldout_sessions,
        "shots_per_label_per_session": shots_per_label,
        "calibration_means": {"label_0": mu0, "label_1": mu1},
        "frozen_threshold": threshold,
        "threshold_source": "calibration sessions only; not updated on held-out data",
        "confusion_matrix_actual_rows_predicted_columns": confusion,
        "heldout_accuracy": sum(float(row["accuracy"]) for row in per_session_accuracy) / len(per_session_accuracy),
        "per_session_heldout_accuracy": per_session_accuracy,
        "heldout_records": heldout_records,
        "limitations": [
            "Seeded toy Gaussian noise and session drift; no instrument data.",
            "The fixed threshold is evaluated only on independent simulated sessions.",
            "Accuracy is a software experiment result, not hardware, device, or mission performance.",
        ],
    }
