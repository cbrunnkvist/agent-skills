# yq — Python TOML+JSON processor (jq wrapper)

| Aspect | Detail |
|--------|--------|
| Lang | Python (wraps `jq` + `tomlkit`) |
| Install | `pip install yq` or `uvx yq ...` |
| In-place | Yes (`-i`) |
| ⚠️ | **Strips comments, reorders keys on write** |

## Usage

`yq -t` converts TOML → JSON → jq → TOML. The `-t` flag specifies TOML output.

```bash
# Read a value
yq -t '.database.server' config.toml

# Set a scalar (in-place)
yq -t -i '.database.server = "127.0.0.1"' config.toml

# Set a number
yq -t -i '.webserver.port = 8443' config.toml

# Add to an array
yq -t -i '.dns.hosts += ["10.13.37.42 qbittorrent.lan"]' pihole.toml

# Replace an array
yq -t -i '.dns.hosts = ["item1", "item2"]' pihole.toml

# Nested path
yq -t -i '.dns.domain = "lan"' pihole.toml
```

## Critical Limitation

`yq` **strips comments and reformats the file** on any write operation. It round-trips through `tomlkit` which re-serializes everything — all comments and original formatting are lost.

**Do NOT use `yq` for:**
- Pi-hole `pihole.toml` (Pi-hole rewrites this file and preserves comments; yq strips them)
- Any human-edited TOML file where comments carry meaning
- Files in version control where cosmetic diff noise matters

**Use `yq` for:**
- CI/CD pipeline patching (no one reads the comments)
- Automated bulk transformations
- Scripted modifications where `toml-cli` is too cumbersome
