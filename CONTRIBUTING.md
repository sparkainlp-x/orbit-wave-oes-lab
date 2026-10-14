# Contributing

Contributions are welcome after the project has been publicly released. Before release, this directory is a review candidate and no pull-request destination exists.

Run the dependency-free tests with `python -m pip install -e '.[test]'` followed by `pytest -q`; run lint with `ruff check src tests`. The optional upstream integration is run with `python -m pip install -e '.[test,oes]'` and `orbit-wave-oes demo --out-dir build/oes-demo --with-oes`; the optional extra pins OES-Resilience v0.6.0.

Keep generated examples explicitly synthetic, preserve the separation between calibration and held-out data, and do not claim physical, quantum, spacecraft, or audio-hardware performance from software-only outputs. Do not commit private binaural captures or personally identifying audio. Any contributed capture fixture must be synthetic or explicitly cleared for public redistribution, with its origin and processing recorded.

Preserve the upstream attributions in `NOTICE`, citations in `CITATION.cff`, and AGPL-3.0-only license. Add tests for behavior changes and update the documentation when assumptions or report fields change.
