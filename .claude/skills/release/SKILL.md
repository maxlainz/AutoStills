---
name: release
description: Cut a version of AutoStills - make ci, version bump, changelog, bitácora, CLAUDE.md, leak-check, annotated tag, CI on the tag.
---

# release

A release is: `version` bumped, changelog, bitácora entry, `CLAUDE.md` updated, vault notes written (rule `obsidian.md`), annotated tag. First version is `v0.1.0`, then plain SemVer (rule `git.md`). In this order:

1. `make ci` green and everything merged into `main` by PR. `gh issue list` read; issues closed by this release referenced in the commit body.
2. Bump `version` in `pyproject.toml` (single source of truth) and `__version__` in the script once it exists. Then `uv sync` so `uv.lock` follows.
3. `CHANGELOG.md`: move `[Unreleased]` into `## [X.Y.Z] - YYYY-MM-DD`; keep an empty `[Unreleased]`.
4. Vault: every new concept of the release has a note (skill `obsidian-vault`). If the vault does not answer, stop and tell the owner.
5. `docs/bitacora/NN-*.md` entry with TL;DR; `CLAUDE.md` state + next step.
6. `make leak-check` once more (rule `repo-publico.md`).
7. Commit `chore(release): vX.Y.Z` by PR, then on merged `main`: `git tag -a vX.Y.Z -m "AutoStills vX.Y.Z" && git push --tags`.
8. Check CI: `gh run list --limit 3`. If it goes red, fix forward with a new patch version; never move the tag.

Never tag with CI red. Never rewrite a pushed tag. The Resolve part cannot be tested in CI: before tagging, ask the owner to run the new version once inside Resolve (rule `resolve.md`).
