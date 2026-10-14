# Orbit–Wave–OES Lab

**Evidence class: SYNTHETIC** (orbit, payload, telemetry and the bundled demo).  
**Physical orbit, spacecraft hardware, quantum devices, NV-center physics, audio hardware and acoustic calibration: UNRUN.**  
**License: AGPL-3.0-only** ([LICENSE](LICENSE)); commercial terms: [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md).

A reproducible, software-only path from a stylized orbital timeline to a synthetic signed-wave payload, fixed-threshold readout, optional OES telemetry replay, and a static evidence passport. It also includes an **offline analog binaural calibration workflow**: generate a stereo test WAV, capture it through the actual analog/audio path with external equipment, then analyze the user-provided two-channel PCM WAV. The tool does not play sound, open an audio device, or claim that any hardware was calibrated.

## Evidence status

| Layer | Status |
|---|---|
| Normalized orbit/environment timeline | **SYNTHETIC** |
| Signed-amplitude sine payload and fixed-threshold readout | **SYNTHETIC** (classical arithmetic) |
| 512-channel telemetry frames and injected events | **SYNTHETIC** |
| Bundled demo and evidence passport | **SYNTHETIC**; SHA-256 checks file consistency only |
| Optional OES-Resilience replay scoring | Software path; inputs are synthetic |
| Analog binaural reference WAV generation | **SYNTHETIC** stimulus |
| Analysis of a user-provided capture WAV | Reports digital relative response only; path authenticity **UNRUN** |
| Real orbit propagator, mission ephemeris, spacecraft sensors | **UNRUN** |
| Quantum device, QKD, NV-center / spin Hamiltonian | **UNRUN** (not modelled) |
| Acoustic / transducer calibration with traceable sensitivity | **UNRUN** |

## Pipeline

1. **Orbit/environment timeline** — normalized circular coordinates and a declared synthetic illumination/shadow window, with a dimensionless thermal proxy. No real orbit propagator, mission ephemeris, spacecraft measurements, or flight environment is used.
2. **Wave/payload model** — binary symbols are represented by the signed-amplitude sine convention associated with Mun Seok Lee's *Digital to Wave* preprint (doi:10.5281/zenodo.21947036). This is a classical sampled waveform test, not an NV-center or quantum-state simulation.
3. **Calibration/readout** — reproduces the supplied seeded Gaussian-noise/session-drift example: a single threshold is fit on calibration sessions and held fixed for independent held-out sessions. Confusion counts and per-session accuracy are recorded.
4. **Telemetry replay** — makes clearly labeled synthetic 512-channel frames and known injected events. The optional `--with-oes` path delegates replay scoring to the public OES-Resilience package instead of claiming a locally invented OES result.
5. **Evidence passport** — packages the protocol, output hashes, metrics, interpretation, and limitations into static HTML plus normalized JSON. SHA-256 verifies file consistency only; it does not prove authorship, timing, measurement validity, or provenance.
6. **Analog binaural capture analysis** — writes a stereo stepped-tone reference WAV; analyzes a separately recorded, uncompressed two-channel PCM WAV for frequency-dependent gain/phase, channel leakage, inter-channel level/phase differences, and clipping. It does not generate correction filters or write to audio hardware.

## Install and run

Python 3.10+ is sufficient for the core simulator, reference-WAV generator, capture analyzer, tests, and passport; these use the standard library.

```bash
python -m pip install -e '.[test]'
pytest -q
orbit-wave-oes demo --out-dir build/demo
```

To use official OES-Resilience replay scoring, install the optional extra (it installs the upstream repository at v0.6.0 and NumPy):

```bash
python -m pip install -e '.[oes]'
orbit-wave-oes demo --out-dir build/demo --with-oes
```

To create an analog binaural test stimulus and analyze a physical capture:

```bash
orbit-wave-oes audio-reference --out build/binaural-reference.wav --sample-rate 48000
# Route/play the reference using your own test setup and record both measurement channels to capture.wav.
# Set the offset to the capture sample corresponding to sample 0 of the reference.
orbit-wave-oes audio-analyze \
  --reference build/binaural-reference.wav \
  --capture capture.wav \
  --capture-offset-samples 0 \
  --out build/binaural-analysis.json
```

The capture must be two-channel, uncompressed PCM WAV at the reference sample rate and long enough to contain the test sequence. `--capture-offset-samples` is the sample index in the recording that corresponds to the beginning of the generated reference. The analysis reports digital relative response; it cannot infer volts, SPL, transducer sensitivity, calibration traceability, or the physical recording path. For a meaningful acoustic calibration, document the interface, transducers, microphone/coupler, placement, gain settings, and any traceable sensitivity calibration outside the tool.

## Reproducibility

The default seed is `20261011`. `demo` writes a timeline CSV, synthetic calibration/readout JSON, OES-compatible calibration/evaluation JSONL, a protocol record, a stereo reference WAV, a run summary, and `evidence-passport/` HTML/JSON. The generated signal values are reproducible for the same code, parameters, and seed; the protocol timestamp is the local UTC write time, is not independently time-verified, and does not establish preregistration. The timestamp, resulting hashes, and optional OES machine/runtime metadata vary between runs.

A complete software-only OES example is bundled at [`examples/synthetic-demo/`](examples/synthetic-demo/). The optional adapter is pinned to upstream OES-Resilience **v0.6.0**. Both detectors recovered the two injected synthetic events; held-out false-positive frame rates were **10.7% (`maxabs`)** and **16.0% (`oes32`)**, above the 5% calibration target. These are synthetic software-path results, not spacecraft measurements.

Upstream real-data evidence is separate from this demo. OES-Resilience v0.5.0 reports a blind, preregistered evaluation on the public NASA SMAP/MSL anomaly dataset; its own README says OES32 did **not** meet its pre-stated success criterion (it beat only EWMA on SMAP, while `maxabs` and CUSUM had higher pooled F1, not significantly). The v0.6.0 release also reports that OES-32-v2 missed its predeclared improvement criterion: test event F1 was 0.213 vs 0.379 for the frozen v1 baseline on SMAP and 0.434 vs 0.435 on MSL; runtime was 2.27× v1 against a 2× limit. These are bounded upstream protocol results, not live monitoring or flight-readiness evidence. This project does not reproduce those evaluations or redistribute the dataset; see [`CITATION.cff`](CITATION.cff) for the software and dataset-paper credits.

The binary readout's calibration set and held-out set are separate. The OES path likewise scores an evaluation replay separately from an event-free calibration replay. The two calibration procedures are distinct and their metrics are not combined.

## Limitations

- Orbit, environmental states, payload signals, injected telemetry events, and the bundled run are **synthetic**. Parameters are demonstration inputs, not validated mission or payload specifications.
- The wave output is classical arithmetic. No quantum device, qubit, NV-center spin, density matrix, quantum error correction, QKD, quantum-secured link, or physical “quantum effect” is simulated or validated.
- A 4,096-element code space, if used by a downstream user, is only a digital code space; it is not evidence of 4,096 resolvable physical states.
- The Digital-to-Wave Part I preprint is credited for the signed-amplitude sine equation; Part II is cited for context only. This project does not reproduce the preprints' physical proposals.
- OES receives synthetic arrays generated by this project. OES replay success is a software-path check only, not evidence of satellite telemetry performance or detector superiority. This project does not claim to beat SMAP/MSL.
- The binaural analyzer only processes a WAV supplied by the user. A WAV file does not authenticate that it came from an analog path, and digital loopback is not the same as acoustic binaural calibration.
- This software does not make operational, clinical, security, safety, mission-readiness, flight, or quantum-advantage claims.

## Acknowledgements and collaborators

Collaboration credit (not authorship of this software; neither person has confirmed authorship or is implied to endorse results):

- **Mun Seok Lee** — credited for the wave-component concept. The signed-amplitude sine equation used here follows Lee's *Digital to Wave* Part I preprint (doi:[10.5281/zenodo.21947036](https://doi.org/10.5281/zenodo.21947036), ORCID [0009-0003-6627-8507](https://orcid.org/0009-0003-6627-8507)). Part II (doi:[10.5281/zenodo.21947108](https://doi.org/10.5281/zenodo.21947108)) is cited for context only.
- **Somnath Laha (CSIR-CMERI)** — credited for related discussion of the satellite / quantum-secured communication concept that motivated the ground-first orbit framing. This repository implements only a classical synthetic orbit timeline and does **not** implement quantum-secured communication, QKD, or any satellite hardware interface. Affiliation is recorded as given; no endorsement of results is implied.

Both appear as `contributors` of type `Other` in [`.zenodo.json`](.zenodo.json), not as `creators`. See also [`NOTICE`](NOTICE) and [`SOURCES.md`](SOURCES.md).

## Attribution and license

Software author: **Jean-François Brisson (Spark AI NLP)**, ORCID [0009-0000-9778-5374](https://orcid.org/0009-0000-9778-5374). The evidence-passport validator bundled under `src/orbit_wave_oes_lab/vendor/` is byte-identical to its v0.1.0 release; its attribution, checksum, and source link are in [`NOTICE`](NOTICE). The optional OES integration calls upstream OES-Resilience v0.6.0; it is not a local reimplementation.

License: **AGPL-3.0-only**; see [`LICENSE`](LICENSE). Commercial use without AGPL obligations: [`COMMERCIAL-LICENSE.md`](COMMERCIAL-LICENSE.md). Third-party content remains under its own stated terms. No preprint text, figures, or PDF is redistributed.

## Review

See [`REVIEW_GUIDE.md`](REVIEW_GUIDE.md) for a short reviewer path, and [`CITATION.cff`](CITATION.cff) / [`.zenodo.json`](.zenodo.json) for citation metadata.
