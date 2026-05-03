# Changelog

All notable user-facing changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added
- Foundation for unified keyboard and popup governance: central modules `app/ui/keybinding_registry.py` and `app/ui/popup_policy.py` are now part of the app structure.

### Changed
- Governance checks now enforce changelog updates only for user- or co-developer-relevant changes; commit/push process hints are local-only and no longer emitted in CI logs.
- Repository path guardrail for absolute JSON path strings was removed to keep enforcement aligned with Namenfit's existing relative-path persistence behavior.
