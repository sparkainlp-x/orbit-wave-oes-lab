# Changelog

## 0.1.1 — 2026-10-14

### Fixed
- Passport manifest records the public repository URL and the build-time `git rev-parse HEAD` commit (null outside a git checkout); the stale "no public repository" note is removed.
- Capture clipping detection is PCM-width-aware (8-bit positive full scale decodes to 127/128 = 0.992); regression test for widths 1-4.
- `analyze_capture` rejects captures longer than 10 minutes before decoding.

### Documentation
- README Reproducibility states the default-seed held-out accuracy (0.742 over 10 sessions) of the synthetic toy classifier with intentionally noisy parameters.

## 0.1.0 — 2026-10-14

### Documentation and packaging
- Professionalization pass: `COMMERCIAL-LICENSE.md`, `REVIEW_GUIDE.md`, `.zenodo.json` (community `spark-ai-nlp`, collaborators as contributors of type Other), evidence-status table, Limitations section, Acknowledgements for Mun Seok Lee (verified wave preprint) and Somnath Laha (CSIR-CMERI; satellite / quantum-secured communication concept credit only).
- README no longer describes the repository as unpublished.

## 0.1.0-rc (local candidate notes)

- Added deterministic normalized orbit/environment and signed-sine payload simulation.
- Added seeded calibration-only midpoint threshold with separate held-out sessions.
- Added optional replay delegation to official OES-Resilience v0.6.0 and an offline evidence passport; v0.6.0 was tested against the candidate's schema-2 synthetic replay bundle.
- Added stereo stepped-tone WAV generation and analysis of user-provided, unverified two-channel PCM captures.
- Added AGPL-3.0-only candidate license, upstream author credits, citations, and Python CI.
- Added current upstream contributor and license verification, Part II Digital-to-Wave context citation, and bounded NASA SMAP/MSL benchmark disclosure.
- No public repository, tag, or external launch has been made.
