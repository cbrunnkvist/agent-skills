# toml-cli — Rust TOML editor

| Aspect | Detail |
|--------|--------|
| Lang | Rust |
| Install | `cargo install toml-cli` or `npx @toml-tools/editor ...` |
| In-place | **No** — always prints to stdout |
| Pros | Format-preserving, comments intact |

## Usage

Format: `toml get <file> <path>` / `toml set <file> <path> <value>`

Path uses dot notation. Arrays use `[index]`.

```bash
# Read a value
toml get config.toml database.server

# Set a scalar
toml set pihole.toml webserver.port 8080

# Set a string (with spaces)
toml set config.toml database.server "my-server.local"

# Add to an array (replaces entire array)
toml set config.toml dns.upstreams "[9.9.9.9, 8.8.4.4]"

# Set nested key
toml set pihole.toml webserver.api.socket true
```

## Critical: toml-cli has no `-i` flag

`toml set` always prints the modified file to stdout. To write in-place:

```bash
toml set src.toml key val > dst.toml && mv dst.toml src.toml
```

## Adding to an array (the common case)

toml-cli cannot directly append to an array — it replaces it. Pipe through the `scripts/append-toml-array.py` helper:

```bash
# Read existing array → append → write back
toml get /etc/pihole/pihole.toml dns.hosts \
  | python3 scripts/append-toml-array.py "10.13.37.180 radarr.lan" \
  | toml set /etc/pihole/pihole.toml dns.hosts
```

Or with inline Python (no helper script):

```bash
EXISTING=$(toml get /etc/pihole/pihole.toml dns.hosts)
toml set /etc/pihole/pihole.toml dns.hosts \
  "$(echo "$EXISTING" | python3 -c "
import sys, json
a = json.load(sys.stdin)
a.append('10.13.37.180 radarr.lan')
print(json.dumps(a))
")"
```
