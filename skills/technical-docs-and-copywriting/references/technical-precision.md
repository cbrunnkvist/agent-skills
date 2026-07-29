# Technical Precision Engine

Use this engine for API references, architecture overviews, CLI guides, setup and deployment procedures, and troubleshooting runbooks. Its purpose is correct action, not persuasion.

## Core Rules

- Use one canonical name for each product, component, API field, command, role, and state. Do not rotate synonyms.
- Prefer active voice: `The client sends the request.` Do not write `The request is sent by the client.`
- Use a concrete verb: `create`, `return`, `reject`, `store`, `retry`, `configure`, `delete`, or `verify`.
- State actors, inputs, outputs, preconditions, and failure conditions. Write `If the token is expired, the server returns 401.`
- Keep steps short. One action per numbered step; target 15–20 words.
- Remove marketing adjectives, rhetorical questions, filler, and conversational asides.
- Keep terminology and code examples aligned. If the API calls a value `workspace_id`, do not call it a project ID in prose.

## Structures

### Searcher-first documentation

Open with a plain-English answer to: what is possible, who it is for, what it requires, and its important limit. Follow with the smallest concrete path.

### Newcomer quickstart

1. List prerequisites and versions.
2. Show setup and authentication without real secrets.
3. Provide one complete, copy-pastable command or program.
4. Show expected output or response.
5. State the next useful action.

### Endpoint reference

Use this order: purpose, method and path, authentication, parameters, request example, response example, status/error behavior, and related links. Mark unknown fields or behavior for validation; do not extrapolate from naming.

### Troubleshooting runbook

Use this order: symptom, likely cause, evidence to collect, diagnostic command, interpretation, corrective action, verification, escalation condition. Make each branch mutually exclusive where possible.

## Code and Response Rules

- Use real syntax for the stated language and label shell commands with `bash` or `sh`.
- Include setup variables and redacted placeholders, for example `API_TOKEN="<token>"`.
- Prefer minimal runnable examples over fragments. Explain omitted production concerns separately.
- Use representative response bodies only when sourced. Otherwise label them `illustrative` and avoid presenting invented fields as API truth.
- State whether retries are safe only when idempotency behavior is known.

## Precision Lint

Reject or rewrite these patterns:

| Avoid | Prefer |
| --- | --- |
| `seamlessly handles errors` | `returns 429 when the rate limit is exceeded` |
| `simply run` | `run` |
| `Note that the client…` | `The client…` |
| `carry out validation` | `validate the request` |
| `this powerful endpoint` | `POST /v1/jobs` |
