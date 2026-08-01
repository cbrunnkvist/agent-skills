# Identity Trace CLI Reference

The CLI depends only on Python's standard library. Invoke it with `python3`:

```text
identity_trace.py doctor [--json]

identity_trace.py run [TARGET]
  [--type auto|email|phone|username|name]
  [--email VALUE]... [--phone VALUE]...
  [--username VALUE]... [--name VALUE]...
  [--birth-date YYYY|YYYY-MM-DD]
  [--sources CSV] [--exclude CSV]
  [--output DIR] [--timeout SECONDS]

identity_trace.py ingest CASE_DIR --input FILE_OR_DASH
identity_trace.py validate CASE_DIR [--json]
```

## Inputs

`TARGET` is a shorthand for one primary identifier. With `--type auto`, the CLI classifies an email, an E.164-like phone number, a whitespace-containing full name, or otherwise a username. Typed flags are repeatable and may be combined. A birth date is auxiliary and cannot be the only input.

Email normalization trims whitespace and lowercases the value. Phone normalization removes formatting and emits `+` followed by digits. Names collapse whitespace. Usernames trim whitespace and an optional leading `@`.

## Sources

| Source | Input | Availability | External destination |
| --- | --- | --- | --- |
| `holehe` | email | `holehe` executable | Service domains queried by Holehe |
| `maigret` | username | `maigret` executable | Profile sites queried by Maigret |
| `phoneinfoga` | phone | `phoneinfoga` executable | Sources queried by PhoneInfoga |
| `github` | email, name, username | `gh` executable | `api.github.com` / `github.com` |
| `gravatar` | email | standard-library HTTPS | `gravatar.com` |
| `hibp` | email | `HIBP_API_KEY` set | `haveibeenpwned.com` |

The default source set is every applicable source. `--sources` limits the set and `--exclude` removes sources after selection. Unknown source names are usage errors.

The GitHub adapter honors the authentication environment already supported by `gh`, including `GH_TOKEN`, but never records token values. HIBP is optional and uses `HIBP_API_KEY` from the active process environment; the CLI does not read `.env` files or accept API keys as command-line arguments. If a user supplies an HIBP key in chat for one run, pass it only through the host's per-process secret/environment mechanism and do not persist it. HTTP requests use `identity-trace-agent-skill` as the user agent.

## Outputs and Exit Codes

Without `--output`, `run` creates `identity-traces/<UTC>-<case suffix>` under the current directory. The directory name never contains an input value. On POSIX systems, directories use mode `0700` and files use mode `0600`.

Progress and warnings go to stderr. Successful commands print a JSON summary to stdout.

- `0`: a case bundle was successfully written or validated; individual sources may still have failed.
- `1`: fatal internal, parsing, integrity, or filesystem failure.
- `2`: invalid command usage or inputs.

An adapter timeout or failure is evidence about collection coverage, not a fatal CLI error. Inspect `case.json` or `report.md` for per-source status.

## Web Result Ingestion

Pass one object or an array through a file or stdin:

```json
{
  "input_ids": ["input-1"],
  "source": "web",
  "query": "\"example-user\"",
  "url": "https://example.test/example-user",
  "title": "Example profile",
  "snippet": "Public search-result excerpt",
  "observed_at": "2026-08-01T00:00:00Z"
}
```

The CLI validates referenced input IDs, derives a stable observation ID, deduplicates repeated ingestion, regenerates `report.md`, and rewrites `SHA256SUMS`.
