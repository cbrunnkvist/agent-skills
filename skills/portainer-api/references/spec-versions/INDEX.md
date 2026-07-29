# Portainer API spec version index

This directory contains full OpenAPI 3.0 YAML specs for multiple Portainer versions and editions, placed side-by-side so the agent can pick the most accurate one for the server it's talking to.

## How to resolve the correct spec

Every Portainer-API task should start with two discovery calls:

```bash
# 1. Get version
curl -fsS -H "X-API-Key: $PORTAINER_API_TOKEN" \
  "$PORTAINER_URL/api/system/version" | jq .
#  → note ServerVersion

# 2. Get edition
curl -fsS -H "X-API-Key: $PORTAINER_API_TOKEN" \
  "$PORTAINER_URL/api/system/version" | jq .
#  → note ServerEdition (1=CE, 2=EE)
```

Then map version + edition → spec file using `TAXONOMY.md`.

> If the detected `ServerVersion` doesn't match any bundled file (e.g. `2.45.0` after the next LTS release), download the exact spec from the official source:
> ```
> https://api-docs.portainer.io/versions/{ce|ee}/{X.Y.Z}.yaml
> ```
> No web search needed — this URL pattern is stable and always serves the published spec for the requested version.

## Available specs

| File | Edition | Version | Stream | Coverage |
|---|---|---|---|---|
| [`ce-2.39-lts.yaml`](ce-2.39-lts.yaml) | CE | 2.39.4 | LTS | 65 paths |
| [`ce-2.43-sts.yaml`](ce-2.43-sts.yaml) | CE | 2.43.0 | STS | 71 paths |
| [`ee-2.39-lts.yaml`](ee-2.39-lts.yaml) | EE | 2.39.4 | LTS | 120 paths |
| [`ee-2.43-sts.yaml`](ee-2.43-sts.yaml) | EE | 2.43.0 | STS | 136 paths |

## How the bundled chunk spec fits in

The sibling directory `../spec/` contains the per-chunk operation index and YAML fragments used by `make specs`. That spec is EE-only at a **single fixed version** (see the header in `../spec/INDEX.md`). Use the versioned full specs here when:

- You need CE endpoint definitions (the chunk spec is EE-only)
- The target server version differs from the currently bundled minor
- You want certainty about which fields/endpoints are available
- An EE-only endpoint listed in the chunk spec returns 404 on a CE server

## Navigation

- `TAXONOMY.md` — release stream model, edition surface diff, version→file resolution algorithm
- `ce-2.39-lts.yaml` — CE spec for 2.39.x LTS (our current server: 2.39.3)
- `ce-2.43-sts.yaml` — CE spec for 2.43.x STS (latest STS)
- `ee-2.39-lts.yaml` — EE spec for 2.39.x LTS
- `ee-2.43-sts.yaml` — EE spec for 2.43.x STS

## Adding new versions

To add a new version:

```bash
curl -sSfLo references/spec-versions/ce-<x>-<stream>.yaml \
  "https://api-docs.portainer.io/versions/ce/<x.y.z>.yaml"
curl -sSfLo references/spec-versions/ee-<x>-<stream>.yaml \
  "https://api-docs.portainer.io/versions/ee/<x.y.z>.yaml"
```

Then update `TAXONOMY.md` with the new entry and operation count.
