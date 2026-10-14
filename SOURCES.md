# Source and license verification notes

Reviewed on **2026-10-14**. Public GitHub API and release metadata were checked through the enabled GitHub connection. The candidate's exact publication target is `sparkainlp-x/orbit-wave-oes-lab`; the GitHub REST endpoint returned 404, and no public repository or remote exists yet.

## Software attribution and licenses

| Source | Checked source | Author / contributor / license fact |
|---|---|---|
| Digital to Wave Testbench | https://github.com/sparkainlp-x/digital-to-wave-testbench and `CITATION.cff` | Jean-François Brisson; AGPL-3.0-only. The public contributor endpoint lists `sparkainlp-x` (17 contributions) and `Copilot` (1); no source code from this repository is vendored. Its CFF identifies Mun Seok Lee's Part I as the signed-amplitude sine equation source and Part II as context only. |
| OES telemetry bench | https://github.com/sparkainlp-x/oes-telemetry-bench | Jean-François Brisson; AGPL-3.0-only; GitHub contributor endpoint lists only `sparkainlp-x` (6 contributions). Referenced, not vendored. |
| OES-Resilience | https://github.com/sparkainlp-x/oes-resilience | Jean-François Brisson; AGPL-3.0-only; GitHub contributor endpoint lists only `sparkainlp-x` (48 contributions). Candidate integration pins v0.6.0, tag commit `79edb72c861fa487ec63e14f9d10d0a55525d513`; v0.6.0 successfully replayed and verified the candidate's existing schema-2 synthetic bundle with the same metrics as the earlier v0.5.0 run. |
| Evidence Passport | https://github.com/sparkainlp-x/evidence-passport | Jean-François Brisson; AGPL-3.0-only; contributor endpoint lists only `sparkainlp-x` (10 contributions). The bundled `evidence_passport.py` is byte-identical to release v0.1.0 (source SHA-256 `1e9d4f9ce9f6d1bbd68f87b9c325d4f9e5a2dc160c1dbc322a1a7e3771cf6b16`); the current `main` file differs, so the older release is explicitly retained and attributed. The candidate `LICENSE` SHA-256 matches the upstream AGPL text. |

The GitHub account `sparkainlp-x` is publicly identified as **Jean-François Brisson**. No additional named human contributor login appeared for the three OES/Evidence Passport repos. The Digital-to-Wave `Copilot` contributor account has no publicly resolvable human identity in the checked API response; it is acknowledged as an upstream contributor entry, not as a human author of this candidate.

The public contributor endpoint is a point-in-time commit-count snapshot, not a complete statement of intellectual authorship. Each source's `CITATION.cff` remains authoritative for the named software author metadata.

## Conceptual and dataset citations

| Source | Checked source | Attribution and use |
|---|---|---|
| Digital to Wave, Part I | https://doi.org/10.5281/zenodo.21947036 | Mun Seok Lee; CC BY 4.0 as recorded in the upstream Digital to Wave Testbench citation metadata. The upstream record identifies this Part I preprint (p. 12) as the signed-amplitude sine equation source. The candidate credits the equation/concept only and redistributes no text or figure. |
| Digital to Wave, Part II | https://doi.org/10.5281/zenodo.21947108 | Mun Seok Lee; corresponding upstream CFF lists CC BY 4.0. The attached PDF itself says “Preprint-Patent pending” and contains no explicit license statement in its extracted text; its title page names Lee while PDF metadata says `PC2510`. Upstream CFF describes it as context-only and says it does not contain the encoded equation. The candidate does not redistribute the PDF or its contents. |
| Orbit–Wave–OES Lab concept brief | User-supplied 2-page brief dated 2026-10-13 | Its author field is **Spark AI NLP**. Used as project requirements/specification only; the separate document is not bundled. The `sparkainlp-x` profile identifies Jean-François Brisson. |
| Earlier NV-diamond concept PDF | User attachment `~EngineeringAnswersFor21_복사본.pdf`; end-page signature identifies Mun Seok Lee | User-provided conceptual context only; not a software license, device validation, or proof that it describes a Pacifica Intelligence/Somnath Laha device. |
| NASA SMAP/MSL anomaly dataset paper | https://doi.org/10.1145/3219819.3219845 | Kyle Hundman, Valentino Constantinou, Christopher Laporte, Ian Colwell, and Tom Soderstrom (2018). Cited by upstream OES-Resilience; this candidate does not redistribute the data or reproduce the evaluation. |

## Bounded OES evidence and version choice

The upstream OES-Resilience v0.5.0 README reports a blind, preregistered public NASA SMAP/MSL evaluation that did not meet its pre-stated criterion: OES32 beat only EWMA on SMAP, while `maxabs` and CUSUM had higher pooled F1 without significant differences. The v0.6.0 release, published 2026-10-13, separately reports OES-32-v2 missing its predeclared improvement criterion: event F1 0.213 vs 0.379 for frozen v1 on SMAP and 0.434 vs 0.435 on MSL; v2 runtime was 2.27× v1 against a 2× limit. These are upstream, protocol- and dataset-specific findings, not operational or flight-readiness claims. The candidate's bundled OES data and its displayed false-positive rates are synthetic.

AGPL-3.0-only is the proposed root license because all four referenced software projects and the vendored Evidence Passport v0.1.0 file use the same license. The CC-BY preprints are cited but not redistributed. This is a compatibility recommendation, not legal advice; author attribution and the root license remain review items before public release.
