#!/usr/bin/env python3

import json
import re
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SKILLS_DIR = ROOT / "skills"
START_MARKER = "<!-- skills:start -->"
END_MARKER = "<!-- skills:end -->"
REPOSITORY = "https://github.com/cbrunnkvist/agent-skills"
DESCRIPTION_LIMIT = 160
SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def parse_scalar(value: str) -> str:
    if value.startswith('"') and value.endswith('"'):
        return str(json.loads(value))
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path.relative_to(ROOT)}: missing YAML frontmatter")

    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(
            f"{path.relative_to(ROOT)}: unterminated YAML frontmatter"
        ) from error

    fields: dict[str, str] = {}
    frontmatter = lines[1:end]
    index = 0

    while index < len(frontmatter):
        line = frontmatter[index]
        index += 1
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue

        key, separator, raw_value = line.partition(":")
        if not separator:
            continue

        value = raw_value.strip()
        if value in {"|", "|-", "|+", ">", ">-", ">+"}:
            block: list[str] = []
            while index < len(frontmatter):
                block_line = frontmatter[index]
                if block_line and not block_line[0].isspace():
                    break
                block.append(block_line)
                index += 1
            block_text = textwrap.dedent("\n".join(block)).strip()
            value = block_text if value.startswith("|") else " ".join(
                block_text.split()
            )

        fields[key.strip()] = parse_scalar(value)

    return fields


def truncate(value: str) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= DESCRIPTION_LIMIT:
        return normalized
    return normalized[: DESCRIPTION_LIMIT - 1].rstrip() + "…"


def markdown_cell(value: str) -> str:
    return value.replace("|", r"\|")


def render_skills() -> str:
    skills: list[tuple[str, str, str]] = []

    for skill_file in SKILLS_DIR.glob("*/SKILL.md"):
        frontmatter = parse_frontmatter(skill_file)
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        directory = skill_file.parent.name

        if not SKILL_NAME.fullmatch(name):
            raise ValueError(
                f"{skill_file.relative_to(ROOT)}: invalid or missing skill name"
            )
        if name != directory:
            raise ValueError(
                f"{skill_file.relative_to(ROOT)}: name must match its directory"
            )
        if not description:
            raise ValueError(
                f"{skill_file.relative_to(ROOT)}: missing description"
            )

        command = f"npx skills add {REPOSITORY} --skill {name}"
        skills.append((name, truncate(description), command))

    if not skills:
        raise ValueError("no skills found")

    rows = [
        "| Skill | Description | Install |",
        "| --- | --- | --- |",
    ]
    for name, description, command in sorted(skills):
        rows.append(
            f"| [{name}](skills/{name}/) | {markdown_cell(description)} "
            f"| `{command}` |"
        )
    return "\n".join(rows)


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    if readme.count(START_MARKER) != 1 or readme.count(END_MARKER) != 1:
        raise ValueError("README.md must contain exactly one skills marker pair")

    start = readme.index(START_MARKER)
    end = readme.index(END_MARKER, start) + len(END_MARKER)
    generated = f"{START_MARKER}\n{render_skills()}\n{END_MARKER}"
    updated = readme[:start] + generated + readme[end:]

    if updated != readme:
        README.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
