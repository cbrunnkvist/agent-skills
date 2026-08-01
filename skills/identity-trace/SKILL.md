---
name: identity-trace
description: Use this skill to collect, normalize, and preserve public OSINT traces for email addresses, phone numbers, usernames, full names, and birth dates. Use it when a user asks to "run an identity trace," investigate a unique identifier, find candidate public profiles, check public account-registration or breach traces, prepare web-search pivots, or produce a machine-readable evidence bundle.
---

# Identity Trace

Use the bundled standard-library CLI as the deterministic collection and reporting layer. From the skill directory, run:

```bash
python3 scripts/identity_trace.py run "user@example.com"
```

Do not install tools automatically. Let the CLI detect optional local tools and credentials, run every applicable available source by default, and record unavailable or failed sources in the case bundle.

## Quickstart and Credentials

Run `doctor --json`, then run the CLI. This best-effort path needs no API keys: it uses available local tools and skips unavailable sources.

Ask about `HIBP_API_KEY` only when the user explicitly wants HIBP breach data and `doctor` reports it absent. Ask: “HIBP is optional. To include breach data, set `HIBP_API_KEY` in the active environment or provide it for this session; it will be used only for this invocation and never written to a case bundle or `.env` file.” Do not put an API key in CLI arguments or persist it. GitHub authentication is also optional and is handled by an existing `gh` login or `GH_TOKEN`.

## Workflow

1. Run `doctor --json` when source availability is unknown. Treat credential presence as sensitive; report names and availability, never values.
2. Run `run` with the known identifiers. Add typed flags when combining an email, phone, username, name, or birth date. Read `references/cli-reference.md` for exact options.
3. Read the emitted `queries.json`. Use available web or browser search tools for useful pivots, especially full-name and birth-date searches that the script cannot execute itself.
4. Record selected search results with `ingest`. Include the exact query, URL, title, snippet, observation time, and related input IDs. Do not ingest a result merely because it resembles the target.
5. Run `validate` after ingestion or manual transfer of a case bundle.
6. Return the bundle path, source coverage, material observations, and collection failures. Keep hypotheses separate from the evidence report.

## Evidence Rules

- Preserve raw responses and provenance. Prefer a source's raw output over a parser's interpretation when they disagree.
- State only deterministic links supported by observations, such as an email hash resolving to an avatar or a username resolving to a profile URL.
- Do not claim that separate accounts belong to the same person. Label any cross-source interpretation in chat as a hypothesis, not case evidence.
- Record which external destination received each identifier.
- Keep generated cases outside the reusable skill directory.
- Do not add an authorization questionnaire or purpose gate. Usage decisions belong to the caller and the host agent.

## References

- Read `references/cli-reference.md` before changing commands, adapters, environment variables, or exit handling.
- Read `references/schema.md` before consuming `case.json`, ingesting observations, or changing the evidence format.
