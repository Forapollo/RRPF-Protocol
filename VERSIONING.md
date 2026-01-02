# Semantic Versioning Contract

RRPF follows semantic versioning with strict backward compatibility guarantees.

## Rules

*   **MAJOR**: Breaking changes to schemas, runner semantics, validation rules, or storage format.
*   **MINOR**: Backward-compatible additions (new helpers, new engines, new stores).
*   **PATCH**: Bug fixes, documentation, internal refactors with zero behavior change.

## Guarantees

*   **0.x.x**: Pre-release stability. Breaking changes may occur but are minimized.
*   **Protocol Frozen**: RRPF protocol law is frozen at `rrp_version = "1.0"`.
*   **Immutability**: Stored payloads from earlier versions in the same major series remain replayable.
