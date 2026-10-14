# Release review checklist

Audit status as of the public repository. A GitHub release / Zenodo deposit is a separate step and is not cut by the professionalization PR.

- [x] Audit upstream CFF author/license metadata; source/license facts are in `NOTICE` and `SOURCES.md`.
- [x] Vendored Evidence Passport matches upstream v0.1.0 byte-for-byte; AGPL license text matches.
- [x] OES-Resilience v0.6.0 replay compatibility checked on the schema-2 synthetic bundle.
- [x] Local test suite and `ruff check src tests` pass.
- [x] Author/maintainer line: Jean-François Brisson (Spark AI NLP), ORCID 0009-0000-9778-5374.
- [x] Root license AGPL-3.0-only, with `COMMERCIAL-LICENSE.md`.
- [x] Public repository `sparkainlp-x/orbit-wave-oes-lab` exists.
- [x] Collaborator credits (Lee, Laha) recorded as non-author acknowledgements / Zenodo contributors of type Other.
- [ ] Zenodo GitHub webhook enabled (required before cutting a release).
- [ ] First public GitHub release / Zenodo deposit (deferred; ask before cutting).
