# Identity Trace Case Schema 1.0

`case.json` is the canonical case record. `report.md` and `SHA256SUMS` are derived artifacts.

## Bundle

```text
<case>/
├── case.json
├── report.md
├── queries.json
├── raw/
└── SHA256SUMS
```

The manifest hashes every regular bundle file except itself using paths relative to the case directory.

## Top-Level Object

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | string | Always `1.0` for this format |
| `case_id` | string | Random, non-PII identifier |
| `started_at`, `completed_at` | RFC 3339 UTC string | Collection interval |
| `configuration` | object | Selected sources, explicit exclusions, and timeout |
| `inputs` | array | Supplied and normalized identifiers |
| `runs` | array | One source execution per applicable input |
| `observations` | array | Normalized evidence records |
| `relationships` | array | Deterministic links supported by observations |
| `queries` | array | Search pivots prepared for an agent |
| `summary` | object | Count-only rollup |

## Records

An input contains `id`, `type`, `value`, and `normalized_value`. Supported types are `email`, `phone`, `username`, `name`, and `birth_date`.

A source run contains:

- `id`, `source`, `input_ids`, and `status`
- `destination`, naming the external service or the upstream tool's destination class
- `started_at` and `completed_at`
- `command`, with secrets omitted or redacted
- `tool_version` when it can be discovered without executing the tool
- `error` when skipped, timed out, or failed
- `raw_artifacts`, each containing a relative path and SHA-256 digest

An observation contains `id`, `input_ids`, `source`, `status`, `kind`, `value`, `url`, `attributes`, `collected_at`, and `raw_artifact`. Valid evidence statuses are `found`, `not_found`, `unknown`, `skipped`, and `error`.

A relationship contains `from`, `to`, `type`, and `source_observation_ids`. Relationships express direct evidence such as `identifier_resolves_to_profile`; they do not express person-level ownership.

Web observations additionally retain the exact `query`, `title`, and `snippet` in `attributes`.

## Consumer Rules

- Treat `raw_artifact` as the evidentiary source and normalized fields as an index.
- Treat `not_found` as source-specific, not proof of global absence.
- Treat `unknown`, `skipped`, and `error` as incomplete coverage.
- Do not infer identity ownership from matching strings alone.
- Verify `SHA256SUMS` before relying on a copied bundle.
