# Changelog

All notable changes to GrantDecay are documented here. The format follows Keep
a Changelog, and the project uses semantic versioning.

## [Unreleased]

### Changed

- Unused surface wording is under review for the next patch.

## [1.0.3] - 2026-06-16

### Fixed

- A window with a single access line no longer reports the entitlement as
  used; usage requires at least one match inside the window.

## [1.0.2] - 2025-10-21

### Added

- Entitlement inventory parsing with per principal grouping.

## [1.0.1] - 2024-07-09

### Fixed

- Access log timestamps with a timezone offset parse correctly across
  daylight saving boundaries.

## [1.0.0] - 2023-09-12

### Added

- Stable CLI contract for decay, window, and version, exit codes 0/1/2.
- Tests pin the window arithmetic and the decay verdicts.

## [0.9.5] - 2022-10-18

### Changed

- Maintenance release: documentation pass and sample refresh.

## [0.9.0] - 2021-08-24

### Added

- Unused surface report: what was granted and never exercised.
- JSON output for pipeline use.

## [0.8.0] - 2020-11-10

### Added

- Decay verdicts per entitlement: used, unused, or unknown.
- Report renderer with stable finding names.

## [0.7.0] - 2019-07-16

### Added

