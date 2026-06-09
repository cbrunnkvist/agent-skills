# tmq — Go TOML query tool

| Aspect | Detail |
|--------|--------|
| Lang | Go |
| Install | `go install github.com/tmq/tmq@latest` |
| In-place | Yes |
| Pros | Zero-dependency binary, fast |

## Usage

```bash
# Read a value
tmq get config.toml database.server

# Set a value
tmq set config.toml database.server "127.0.0.1"

# Set a number
tmq set config.toml webserver.port 8080
```
