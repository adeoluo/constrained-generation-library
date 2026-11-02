# Changelog

All notable changes to this project are documented here. The file is generated
from Conventional Commits by [git-cliff](https://git-cliff.org) when a release is cut
with `make cut-release`.

## Unreleased

### Documentation

- Standard README structure and language framing (#6)
- Horizontal layered architecture diagram
- Compact horizontal architecture diagram

### Build and CI

- Run CodeQL on main and on a weekly schedule only

## [0.1.0] 2026-11-01

### Features

- Implement schema-constrained generation via finite automata (#1)

### Bug fixes

- Match JSON-escaped property names and enum values (#3)

### Documentation

- Add explicit comparison scope and honest baseline framing (#2)

### Tests

- Add independent jsonschema differential validation and adversarial tests (#5)

### Maintenance

- Initialize repository with license and overview
- Remove Dependabot configuration

### Bench

- Add large-workload scale benchmark (#4)
