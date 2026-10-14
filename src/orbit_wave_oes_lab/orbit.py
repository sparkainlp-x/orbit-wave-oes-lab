"""Stylized synthetic orbit/environment timeline; no physical ephemeris is used."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class OrbitConfig:
    """Dimensionless circular-orbit display settings for the software demo."""

    steps: int = 80
    period_steps: int = 40
    sample_interval_seconds: int = 60
    shadow_start_fraction: float = 0.35
    shadow_end_fraction: float = 0.65
    start_time_utc: str = "2026-10-11T00:00:00+00:00"

    def validate(self) -> None:
        for name, value, minimum in (
            ("steps", self.steps, 2),
            ("period_steps", self.period_steps, 2),
            ("sample_interval_seconds", self.sample_interval_seconds, 1),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")
        if not (0.0 <= self.shadow_start_fraction < self.shadow_end_fraction <= 1.0):
            raise ValueError("shadow fractions must satisfy 0 <= start < end <= 1")
        try:
            parsed = datetime.fromisoformat(self.start_time_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("start_time_utc must be an ISO-8601 timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError("start_time_utc must include a UTC offset")


def generate_timeline(config: OrbitConfig | None = None) -> list[dict[str, object]]:
    """Return a deterministic orbit-shaped timeline in normalized, arbitrary units.

    The shadow window and first-order thermal proxy are illustrative choices.
    They are not an orbit propagator or a model of a particular spacecraft.
    """
    if config is None:
        config = OrbitConfig()
    config.validate()
    start = datetime.fromisoformat(config.start_time_utc.replace("Z", "+00:00")).astimezone(timezone.utc)
    thermal_index = 0.35
    output: list[dict[str, object]] = []
    for index in range(config.steps):
        turn = (index % config.period_steps) / config.period_steps
        phase = 2.0 * math.pi * turn
        x, y = math.cos(phase), math.sin(phase)
        in_shadow = config.shadow_start_fraction <= turn < config.shadow_end_fraction
        illumination = 0.0 if in_shadow else 1.0
        target_thermal = 0.25 + 0.55 * illumination + 0.08 * math.sin(phase)
        thermal_index += 0.22 * (target_thermal - thermal_index)
        # A narrow synthetic environment pulse is included to exercise replay code.
        radiation_proxy = 0.10 + (0.65 if 0.72 <= turn < 0.77 else 0.0)
        stamp = start + timedelta(seconds=index * config.sample_interval_seconds)
        output.append(
            {
                "frame_index": index,
                "timestamp_utc": stamp.isoformat(timespec="seconds"),
                "orbit_phase_rad": phase,
                "orbit_phase_fraction": turn,
                "x_normalized": x,
                "y_normalized": y,
                "shadow_window": in_shadow,
                "illumination_fraction": illumination,
                "thermal_index_arbitrary": thermal_index,
                "environment_pulse_proxy_arbitrary": radiation_proxy,
                "evidence_class": "SYNTHETIC",
            }
        )
    return output
