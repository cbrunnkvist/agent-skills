---
name: mtgx
description: Build, query, merge, validate, and manipulate Maltego MTGX investigation graphs. Use when working with mtgx or common typo mgtx files, Maltego, .mtgx archives, GraphML for Maltego, entity/link graph creation, OSINT graph workflows, Maltego archive validation, image embedding in Maltego entities, or converting JSON/NDJSON graph data into Maltego-native files.
---

# MTGX

Use the bundled stdlib-only CLI for Maltego MTGX graph work:

```bash
python3 <skill>/scripts/mtgx.py --help
```

Prefer `python3 <skill>/scripts/mtgx.py ...` as the primary execution path. If the active environment has managed Python constraints, `uv run <skill>/scripts/mtgx.py ...` is acceptable as a fallback only.

Do not install packages, create virtual environments, or debug `uvx` for this skill. The CLI is a single Python file and depends only on the standard library.

## Workflow

1. Read `references/cli-reference.md` when creating, querying, merging, exporting, importing, or embedding images.
2. Read `references/maltego-mtgx-format.md` before changing MTGX serialization, validating Maltego archive compatibility, or diagnosing Maltego import/open errors.
3. Use JSON or NDJSON as the editable graph input format, then create a `.mtgx` with the CLI.
4. Run `validate` on any `.mtgx` before handing it back to the user.
5. Keep investigation-specific evidence, logos, generated archives, and article text outside the skill unless the user explicitly asks for a project-specific graph.

## Guardrails

- Keep MTGX archives minimal: only `version.properties` and `Graphs/Graph1.graphml`.
- Do not pack `Icons/`, `Entities/`, `Graphs/Graph1.properties`, `META-INF/MANIFEST.MF`, source articles, project logos, or generated investigation files into reusable skills.
- Mark uncertain claims in labels with `[UNVERIFIED]` and use red dashed links when representing them.
- Prefer Maltego standard property names such as `person.fullname`, `organization.name`, `title`, `location.name`, `date`, `url`, and `description`.
