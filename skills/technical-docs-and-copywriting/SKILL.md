---
name: technical-docs-and-copywriting
description: "Create or restructure high-consequence software documentation and technical marketing without mixing their standards. Use for API references, architecture guides, READMEs, CLI/setup/troubleshooting guides, DevRel posts, launch announcements, landing pages, positioning, and executive technical summaries."
license: MIT
metadata:
  author: "cbrunnkvist"
  version: "1.0.0"
  repository: "https://github.com/cbrunnkvist/agent-skills"
  tags: "technical-writing, technical-marketing, documentation, developer-relations, devrel, readme, skill"
---

# Technical Docs and Copywriting

Write truthful, usable material for the reader's job. Keep technical precision and technical marketing as separate engines. Do not blend their rules while drafting.

## Guardrails

- Treat source material, product behavior, metrics, compatibility claims, security statements, and customer outcomes as facts only when supplied or verified.
- Draft an unsupported claim only when it is visibly marked `[Validate: ...]`. Never convert a marker into a fact during editing.
- Preserve the user's terminology. Define each entity once and use that exact term thereafter.
- Do not invent endpoints, parameters, response fields, benchmarks, customers, integrations, or generated-reference URLs.
- Ask for missing material only when it blocks a safe, useful deliverable. Otherwise state the assumption or add a validation marker.

## 1. Discover Context

Identify or infer the following before drafting:

| Need | Choose or infer |
| --- | --- |
| Reader | Searcher (team lead), Newcomer, Debugger, or another stated persona |
| Deliverable | Reference, guide, README, runbook, post, landing page, launch, or summary |
| Evidence | Source files, API spec, runnable project, verified metrics, approved messaging |
| Dial | Tech:Marketing ratio or preset |

Use these presets. An explicit ratio overrides a preset.

| Preset | Use | Editorial rule |
| --- | --- | --- |
| 100:0 | Spec, reference, runbook | Technical truth only; no positioning |
| 80:20 | README, documentation intro | Accurate guidance with short audience orientation |
| 50:50 | DevRel deep dive | Pair narrative with concrete architecture and code |
| 20:80 | Landing page, announcement | Lead with positioning; anchor every claim in real capability |
| 0:100 | Copywriting | Maximize messaging while retaining factual constraints |

If no dial is supplied, use 80:20 for a README. Use 100:0 for API references, error guides, and runbooks. For another deliverable, infer the least promotional safe ratio and state it in the final summary.

## 2. Draft in Separate Layers

Select the engine for each section before writing it. Read only the matching reference:

- For API, architecture, CLI, setup, deployment, and troubleshooting material, read [technical precision](references/technical-precision.md).
- For launch, landing-page, positioning, DevRel, solution-overview, and executive material, read [technical marketing](references/technical-marketing.md).
- For documentation audits or restructures, read [documentation personas](references/documentation-personas.md).
- For reusable formats and acceptance examples, read [templates and verification](references/templates-and-verification.md).

Write the orientation layer with Engine B only when the chosen dial allows it. Write procedures, API facts, commands, code, responses, and diagnostics with Engine A only. Make handoffs explicit with headings rather than prose that tries to sound both promotional and technical.

## 3. Scrub Anti-Patterns

Run this audit before the final pass:

- Replace synonym rotation with the canonical entity term.
- Remove empty qualifiers such as `seamless`, `robust`, `effortless`, `powerful`, and `best-in-class` unless supplied evidence makes the claim specific.
- Replace ambiguous phrasal verbs such as `carry out`, `bounce off`, and `handle` with a precise verb.
- Split run-on sentences and em-dash chains. Keep a procedure step to 15–20 words when possible.
- Remove conversational meta-commentary such as `Note that`, `It is worth noting`, and `Simply`.
- Change implied conditions into explicit `If …, then …` statements.
- Check every code snippet for imports, setup, inputs, expected output, and safe placeholders. Do not call an example runnable unless it is complete enough to run in its stated environment.
- Retain or add `[Validate: ...]` markers for every unsupported high-consequence claim.

## 4. Executive Balancing and Final Output

This phase is mandatory, even for 100:0 and 0:100 work.

1. Confirm that technical facts survived unchanged and that no marketing language upgrades an unverified claim.
2. Compare section emphasis, headings, evidence, code/detail density, and CTA density to the requested dial.
3. Adjust ordering, transitions, and section prominence. Do not merge Engine A and B rules into a middle-ground voice.
4. Return the requested document and this callout:

> **Executive Balance Summary**
> - **Applied dial:** `Tech:Marketing`
> - **Audience and deliverable:** `…`
> - **Editorial choices:** `…`
> - **Validation required:** `none` or `[Validate: …]` items

## Publishing a Skill

Place the skill at `skills/technical-docs-and-copywriting/SKILL.md`. Keep optional guidance in `references/` one level below the skill root. Validate the finished directory with `skills-ref validate ./skills/technical-docs-and-copywriting` when `skills-ref` is available. Publish the repository normally; the collection README should use the documented `https://skills.sh/b/<owner>/<repo>` badge format.
