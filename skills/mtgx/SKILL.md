---
name: mtgx
description: Build, query, merge, validate, and manipulate Maltego MTGX investigation graphs. Use when working with mtgx or common typo mgtx files, Maltego, .mtgx archives, GraphML for Maltego, entity/link graph creation, OSINT graph workflows, Maltego archive validation, image embedding in Maltego entities, or converting JSON/NDJSON graph data into Maltego-native files.
---

# Maltego Graphs (.mtgx)

## Basic Investigative Graphing

Start every investigation by modeling the question, not by looking for a pre-existing Maltego entity type. The absence of a built-in type is never a reason to leave a material concept out of the graph.

1. State the investigative question and identify the things, events, and relationships needed to answer it. For example: people, organizations, locations, accounts, assets, transactions, communications, and control/ownership/use relationships.
2. Use the closest existing general type when it preserves the distinction needed for the investigation. A single luxury yacht can be a general `Asset` with properties such as `asset.kind = yacht`, name, IMO/MMSI, owner, and source. Do not create a `Yacht` type merely for a better icon or label.
3. Add a custom entity type when a category is repeated or analytically material and a generic type would make the graph harder to query, interpret, transform, or present. Examples include a `ScamCenter` when several locations must be distinguished from ordinary offices/hotels, `RecruitmentCompound` when it has recurring evidence fields and relationships, or `CryptoWallet` when it needs chain-specific identifiers and transaction links.
4. Give each custom type a clear singular name, one primary value, only the properties that recur or affect analysis, and an appropriate icon. Add relationship labels that state what the evidence supports, such as `operates from`, `recruits for`, `controls`, `owns`, or `transferred funds to`.
5. Keep one-off facts as properties, notes, or generic entities. Promote them to a custom type only when the distinction has a real analytical payoff. Avoid both extremes: forcing everything into `Phrase`/`Asset`, and creating a bespoke type for every individual object.
6. Add evidence and uncertainty at the same time as the node or link: source URL, retrieval date, relevant quote/identifier, and confidence. A graph is an evidence model, not an assertion engine.

Create custom Maltego types in the target Maltego configuration or a separately maintained type library. Reference those types from MTGX/JSON input, but do not pack `Entities/` or icon files into a minimal MTGX archive.

## Capability Boundary

This skill and its CLI build, inspect, query, merge, and validate MTGX files. They do **not** control the interactive Maltego application and cannot run Maltego Transforms, select graph entities, use graph views/layouts, create types through the GUI, or retrieve Transform results.

When a workflow calls for a Transform, clearly distinguish the two roles:

- **Interactive Maltego user:** runs the Transform and exports, shares, or otherwise supplies its resulting entities/links.
- **This skill/CLI:** models supplied evidence or exported data, prepares JSON/NDJSON, creates or edits the MTGX, and validates its file structure.

Do not claim that a Transform was run, that a visual graph result was observed, or that a type was installed in Maltego unless the user provided that result or performed the interactive action. An agent may obtain data from separately available documented sources when asked and permitted, but that is not a Maltego Transform.

Use the bundled stdlib-only CLI for Maltego MTGX graph work:

```bash
python3 <skill>/scripts/mtgx.py --help
```

Prefer `python3 <skill>/scripts/mtgx.py ...` as the primary execution path. If the active environment has managed Python constraints, `uv run <skill>/scripts/mtgx.py ...` is acceptable as a fallback only.

Do not install packages, create virtual environments, or debug `uvx` for this skill. The CLI is a single Python file and depends only on the standard library.

## Workflow

1. Apply **Basic Investigative Graphing** above: choose general versus custom entity types before adding data.
2. Read `references/cli-reference.md` when creating, querying, merging, exporting, importing, or embedding images.
3. Read `references/maltego-mtgx-format.md` before changing MTGX serialization, validating Maltego archive compatibility, or diagnosing Maltego import/open errors.
4. Read `references/cryptocurrency-investigations-howto.md` before modeling cryptocurrency fund flows or importing blockchain-transfer data.
5. Use JSON or NDJSON as the editable graph input format, then create a `.mtgx` with the CLI.
6. Run `validate` on any `.mtgx` before handing it back to the user.
7. Keep investigation-specific evidence, logos, generated archives, and article text outside the skill unless the user explicitly asks for a project-specific graph.

## Guardrails

- Keep MTGX archives minimal: only `version.properties` and `Graphs/Graph1.graphml`.
- Do not pack `Icons/`, `Entities/`, `Graphs/Graph1.properties`, `META-INF/MANIFEST.MF`, source articles, project logos, or generated investigation files into reusable skills.
- Mark uncertain claims in labels with `[UNVERIFIED]` and use red dashed links when representing them.
- Prefer Maltego standard property names such as `person.fullname`, `organization.name`, `title`, `location.name`, `date`, `url`, and `description`.

## Security Boundary

- **Path traversal**: All file-path inputs (`logo_dir`, `img_path`, `image`) are resolved and validated to remain within the intended directory before reading.
- **File-type restriction**: The `embed` command and logo embedding only accept image files with known extensions (png, jpg, jpeg, gif, bmp, svg, ico, webp).
- **Size limits**: Input data is capped at 50 MB; individual images at 10 MB; entity count at 100 000; string values at 10 000 characters.
- **Input sanitization**: Control characters are stripped from all string values before they enter the graph model.
- **XML safety**: External entity and DTD declarations are rejected before parsing.
- **No unbounded reads**: All file and stdin reads are bounded by size limits.
