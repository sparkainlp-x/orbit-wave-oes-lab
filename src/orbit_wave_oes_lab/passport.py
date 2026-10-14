"""Thin adapter around the attributed upstream Evidence Passport validator."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .vendor import evidence_passport


def build_passport(manifest_path: str | Path, output_dir: str | Path) -> tuple[Path, Path]:
    """Validate manifest/artifact hashes, then write static HTML and normalized JSON."""
    manifest_path = Path(manifest_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    report: dict[str, Any] = evidence_passport.load_and_validate(manifest_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / f"{report['run_id']}.html"
    json_path = output_dir / f"{report['run_id']}.normalized.json"
    html_path.write_text(evidence_passport.render_html(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return html_path, json_path
