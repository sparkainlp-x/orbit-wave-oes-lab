import math

import pytest

from orbit_wave_oes_lab.orbit import OrbitConfig, generate_timeline
from orbit_wave_oes_lab.wave import encode_symbol, run_threshold_experiment


def test_orbit_timeline_is_reproducible_and_dimensionless():
    config = OrbitConfig(steps=40, period_steps=20)
    first = generate_timeline(config)
    second = generate_timeline(config)
    assert first == second
    assert len(first) == 40
    assert first[0]["x_normalized"] == pytest.approx(first[20]["x_normalized"])
    assert first[0]["y_normalized"] == pytest.approx(first[20]["y_normalized"])
    assert all(row["evidence_class"] == "SYNTHETIC" for row in first)
    assert all(0.0 <= row["thermal_index_arbitrary"] <= 1.0 for row in first)


def test_invalid_shadow_window_is_rejected():
    with pytest.raises(ValueError):
        generate_timeline(OrbitConfig(shadow_start_fraction=0.8, shadow_end_fraction=0.2))


def test_wave_symbols_are_classical_and_dimensionless():
    zero = encode_symbol(0)
    one = encode_symbol(1)
    assert zero["amplitude_arbitrary"] == 0.0
    assert one["amplitude_arbitrary"] == 1.0
    assert one["phase_rad"] == pytest.approx(math.pi / 4)
    assert len(one["samples"]) == 64
    assert "classical" in one["scope"]
    with pytest.raises(ValueError):
        encode_symbol(2)


def test_threshold_is_frozen_and_heldout_sessions_are_reported():
    result = run_threshold_experiment(seed=20261011)
    repeat = run_threshold_experiment(seed=20261011)
    assert result == repeat
    assert result["threshold_source"].startswith("calibration sessions only")
    assert len(result["per_session_heldout_accuracy"]) == 10
    assert len(result["heldout_records"]) == 2000
    matrix = result["confusion_matrix_actual_rows_predicted_columns"]
    assert sum(sum(row) for row in matrix) == 2000
    assert 0.0 <= result["heldout_accuracy"] <= 1.0
