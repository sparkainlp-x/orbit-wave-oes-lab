"""Command-line entry point for the Orbit–Wave–OES Lab candidate."""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .audio import analyze_capture, write_reference_wav
from .pipeline import run_demo
from .wave import DEFAULT_SEED


def _save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orbit-wave-oes",
        description="Synthetic orbit/wave/OES demo and offline stereo capture analyzer; no audio device is opened.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run the synthetic orbit-to-wave/readout/telemetry/passport pipeline")
    demo.add_argument("--out-dir", type=Path, default=Path("build/demo"))
    demo.add_argument("--seed", type=int, default=DEFAULT_SEED)
    demo.add_argument("--steps", type=int, default=80)
    demo.add_argument("--with-oes", action="store_true", help="delegate scoring to installed official OES-Resilience")

    reference = sub.add_parser("audio-reference", help="write a digital stereo calibration stimulus WAV and protocol sidecar")
    reference.add_argument("--out", type=Path, required=True)
    reference.add_argument("--sample-rate", type=int, default=48_000)
    reference.add_argument("--tone-level", type=float, default=0.25)

    analysis = sub.add_parser("audio-analyze", help="analyze a user-provided stereo PCM WAV capture against a reference")
    analysis.add_argument("--reference", type=Path, required=True)
    analysis.add_argument("--capture", type=Path, required=True)
    analysis.add_argument("--capture-offset-samples", type=int, default=0)
    analysis.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = run_demo(args.out_dir, seed=args.seed, steps=args.steps, with_oes=args.with_oes)
            print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
            return 0
        if args.command == "audio-reference":
            protocol = write_reference_wav(args.out, sample_rate_hz=args.sample_rate, tone_level=args.tone_level)
            print(json.dumps({"reference_wav": str(args.out.resolve()), "protocol_sidecar": str(args.out.with_suffix(args.out.suffix + '.json').resolve()), "sample_rate_hz": protocol["sample_rate_hz"], "tone_segments": len(protocol["segments"]), "scope": protocol["warning"]}, indent=2))
            return 0
        if args.command == "audio-analyze":
            report = analyze_capture(args.reference, args.capture, capture_offset_samples=args.capture_offset_samples)
            _save_json(args.out, report)
            print(json.dumps({"status": "analyzed_user_provided_wav", "evidence_class": report["evidence_class"], "report": str(args.out.resolve()), "hardware_calibration_claimed": False}, indent=2))
            return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
