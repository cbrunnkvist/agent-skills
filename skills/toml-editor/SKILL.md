---
name: toml-editor
description: Edit TOML files programmatically using yq, tmq, or toml-cli. Use when asked to edit .toml files, modify pyproject.toml, update pihole.toml, or any TOML operation. Triggers on "edit toml", "modify .toml", "toml file", "update pyproject.toml", "pihole.toml".
license: MIT
compatibility: "Requires Python 3.11+ (for tomllib validation) and one of: yq (pip/uvx), toml-cli (cargo/npx), or tmq (go install)."
allowed-tools:
  - Bash(python3:*)
  - Bash(toml:*)
metadata:
  version: "1.1"
---

# TOML Editor

Edit `.toml` files without shell escaping issues. Three tools available:

| Tool | Lang | In-place | Pros | Reference |
|------|------|----------|------|-----------|
| **toml-cli** | Rust | No (prints) | Format-preserving, comments intact | [`references/toml-cli.md`](references/toml-cli.md) |
| **yq** | Python | Yes (`-i`) | jq-like syntax, widely known | [`references/yq.md`](references/yq.md) |
| **tmq** | Go | Yes | Zero-dependency binary, fast | [`references/tmq.md`](references/tmq.md) |

**Recommendation:** Prefer `toml-cli` for Pi-hole configs and other human-edited files where comment preservation matters. Prefer `yq -t -i` for automated transformations (CI, scripts). Pull the reference doc for your chosen tool above.

## Installation (one-time)

```bash
# toml-cli — Rust
cargo install toml-cli
# or no-install: npx @toml-tools/editor set config.toml key "value"

# yq — Python
pip install yq
# or no-install: uvx yq -t -i '.key = "value"' config.toml

# tmq — Go
go install github.com/tmq/tmq@latest
```

## Workflows

### Adding a custom DNS record to Pi-hole v6

```bash
yq -t -i '.dns.hosts += ["10.13.37.180 myservice.lan"]' /etc/pihole/pihole.toml
pihole restartdns
```

### Patching pyproject.toml

```bash
# Add a dependency
yq -t -i '.project.dependencies += ["httpx>=0.27"]' pyproject.toml

# Add optional dependency group
yq -t -i '.project.optional-dependencies.dev = ["pytest>=8"]' pyproject.toml

# Set Python version requirement
yq -t -i '.project.requires-python = ">=3.11"' pyproject.toml
```

### Array append with toml-cli

```bash
toml get /etc/pihole/pihole.toml dns.hosts \
  | python3 scripts/append-toml-array.py "10.13.37.180 radarr.lan" \
  | toml set /etc/pihole/pihole.toml dns.hosts
```

## Validation

```bash
python3 scripts/validate-toml.py file.toml
# or inline:
python3 -c "import tomllib; tomllib.load(open('file.toml','rb'))"
```

## Safety

- **Back up** before bulk edits: `cp file.toml file.toml.bak`
- **Validate** after every edit
- **`yq` strips comments and reorders keys** — use `toml-cli` when formatting matters
- **toml-cli has no `-i`** — pipe to temp file and rename
- **No tool does true inline editing** — they rewrite the file. Use version control.
