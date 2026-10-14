# Release review checklist

This file records the completed audit and remaining review gates for the local candidate. It is not a publication approval.

- [x] Audit the four upstream software repositories' current CFF author/license metadata and GitHub contributor API results; source/license facts are recorded in `NOTICE` and `SOURCES.md`.
- [x] Verify that the vendored Evidence Passport file matches upstream v0.1.0 byte-for-byte and that the bundled AGPL license text matches upstream.
- [x] Test OES-Resilience v0.6.0 replay compatibility against the existing schema-2 sample; reproduce the held-out synthetic results.
- [x] Run the full local test suite (11 passed on Python 3.12.3) and Ruff (`ruff check src tests`: passed).
- [ ] Confirm the proposed author/maintainer line: **Jean-François Brisson (Spark AI NLP)**. The user-provided concept brief names Spark AI NLP; the public `sparkainlp-x` profile identifies Jean-François Brisson.
- [ ] Confirm **AGPL-3.0-only** for the new combined work and retained vendor code.
- [ ] Review the final complete tree, especially the updated attributions, OES upstream-result caveats, synthetic-data boundaries, and analog-capture limitations. Pyright reports 14 type diagnostics only in the unchanged vendored Evidence Passport v0.1.0 source; no candidate-owned source diagnostics were reported.
- [ ] Explicitly approve public GitHub creation/push and the exact repository name `sparkainlp-x/orbit-wave-oes-lab`.
- [ ] Public release remains blocked until the above review and approval are complete.

GitHub account `sparkainlp-x` is Jean-François Brisson. The target repository lookup returned 404 on 2026-10-14; no repository, remote, commit, tag, push, or public record has been created. Publication remains pending the user's review and explicit confirmation.
