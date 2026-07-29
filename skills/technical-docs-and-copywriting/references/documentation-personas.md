# Documentation Persona Restructure

Use this guide to audit existing documentation or design a new documentation set. Serve personas in this order: Searcher, Newcomer, Debugger. The CTO/architect is lowest priority; add decision material only when it does not displace the first three.

## 1. Searcher: Plain-English Feasibility

Place an answer near the start of the landing page or overview:

- What the library or API enables.
- Who should use it.
- The smallest viable integration.
- Required systems, account types, or constraints.
- The most important unsupported use case or limitation.

Avoid jargon until it is necessary. Link to detail rather than placing a reference manual before the feasibility answer.

## 2. Newcomer: Runnable First Success

Provide a quickstart that a developer can copy and run. Include prerequisites, authentication, installation, a complete example, expected response or output, and the next task. Keep secrets as placeholders and give exact cleanup or safety warnings for destructive examples.

## 3. Debugger: Precise Navigation

Make it easy to locate exact behavior in an existing integration:

- Link error names, status codes, fields, methods, and configuration keys to API/reference pages.
- Prefer generated reference pages from inline comments, OpenAPI, typed docstrings, or an equivalent maintained source of truth.
- Verify every link. If generated pages do not exist, name the missing source and build step instead of linking to an imagined URL.
- Pair each error with likely cause, evidence, corrective action, and escalation condition.

## Audit Checklist

For each relevant product surface, establish or repair:

- [ ] Authentication guide: supported methods, setup, scope/role behavior, rotation or expiry, redacted examples, and failure handling.
- [ ] Quickstart guide: prerequisites, installation, one runnable path, expected result, and next action.
- [ ] Endpoint definitions: purpose, method/path, auth, inputs, examples, responses, errors, and related operations.
- [ ] Code snippets: language label, complete context, safe placeholders, and stated runtime assumptions.
- [ ] Example responses: sourced or explicitly illustrative; redact secrets and unstable identifiers.

## Ordering Test

An unfamiliar team lead should determine feasibility without reading developer terminology. A new developer should reach a first successful result before reading the full API. A maintainer should reach a named error or field from a relevant hyperlink.
