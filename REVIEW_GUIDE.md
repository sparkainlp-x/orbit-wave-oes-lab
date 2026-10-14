# Review guide

A short path for reviewers. Everything below is software-only; orbit, wave, telemetry and the bundled demo are **SYNTHETIC**. Physical orbit propagation, spacecraft hardware, quantum devices, NV-center physics, audio hardware and acoustic calibration are **UNRUN**.

## 1. What this is

A research prototype that chains a stylized orbital timeline, a classical signed-amplitude sine payload encoding, a fixed-threshold synthetic readout, optional OES-Resilience replay scoring, a static evidence passport, and offline analysis of a user-provided stereo PCM WAV. It is not flight software, not a quantum device, and not a calibrated audio instrument.

## 2. Five-minute check

```bash
python -m pip install -e '.[test]' ruff
ruff check src tests
python -m pytest -q
orbit-wave-oes demo --out-dir /tmp/orbit-wave-demo
```

Expected: ruff reports all checks passed; core tests pass (the optional OES integration test skips unless `.[oes]` is installed); the demo writes a timeline, synthetic readout, protocol, reference WAV and `evidence-passport/` under `/tmp/orbit-wave-demo`.

## 3. Optional OES path

```bash
python -m pip install -e '.[test,oes]'
python -m pytest -q
orbit-wave-oes demo --out-dir /tmp/orbit-wave-oes --with-oes
```

Expected: all tests pass; the evidence passport reports `evidence_class` `synthetic` and `bundle_consistent` true. Held-out false-positive rates in the bundled example are above the 5% calibration target; they are software-path results only.

## 4. What not to claim

- No real orbit, spacecraft measurement, or mission ephemeris.
- No quantum device, QKD, quantum advantage, or NV-center simulation.
- No beat of the NASA SMAP/MSL benchmark; upstream OES-Resilience reports that its own criteria were not met.
- No authenticated analog path or acoustic calibration from a WAV file alone.
