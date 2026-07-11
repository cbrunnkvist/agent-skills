# Agent Instructions

## Repository Scope
- This is a personal collection of agent skills under `skills/`.
- Keep skill edits scoped to the requested skill directory unless the user asks for repository-wide changes.
- Treat untracked skill directories as user-owned unless the task explicitly concerns them.

## Skills.sh Checks
- Use the README badge format from `https://skills.sh/docs`: `https://skills.sh/b/<owner>/<repo>` linking to `https://skills.sh/<owner>/<repo>`.
- When diagnosing skills.sh discoverability, check both the collection page and direct skill page before changing metadata.
- Do not assume `/search` or `npx skills find` reflects the same state as direct collection or skill pages; skills.sh has shown route/search/cache inconsistencies.
- Do not manufacture install telemetry with repeated local installs. Use direct page state, install counts, and documented search behavior as repro evidence instead.

## Publishing Notes
- The canonical public repo is `cbrunnkvist/agent-skills`.
- Prefer exact, minimal commits for metadata or skill documentation changes.
