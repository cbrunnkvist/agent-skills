# MTGX CLI Reference

Run the bundled CLI directly:

```bash
python3 <skill>/scripts/mtgx.py create input.json -o output.mtgx
python3 <skill>/scripts/mtgx.py validate output.mtgx
```

Use `uv run <skill>/scripts/mtgx.py ...` only as a managed-Python fallback. Do not use `uvx`; there is no package to install.

## Commands

```bash
# Build from JSON/NDJSON
python3 <skill>/scripts/mtgx.py create input.json -o output.mtgx

# Export as structured data
python3 <skill>/scripts/mtgx.py export output.mtgx --format json
python3 <skill>/scripts/mtgx.py export output.mtgx --format ndjson
python3 <skill>/scripts/mtgx.py export output.mtgx --format graphml

# Query entities
python3 <skill>/scripts/mtgx.py query output.mtgx --filter "type=maltego.Person"
python3 <skill>/scripts/mtgx.py query output.mtgx --filter "value~=Mauer"

# Neighborhood and path queries
python3 <skill>/scripts/mtgx.py query output.mtgx --neighborhood n1 --depth 2
python3 <skill>/scripts/mtgx.py query output.mtgx --path n1 n10

# Merge, inspect, validate
python3 <skill>/scripts/mtgx.py merge a.mtgx b.mtgx -o merged.mtgx
python3 <skill>/scripts/mtgx.py diff a.mtgx b.mtgx
python3 <skill>/scripts/mtgx.py stats output.mtgx
python3 <skill>/scripts/mtgx.py timeline output.mtgx
python3 <skill>/scripts/mtgx.py validate output.mtgx

# Edit an existing graph
python3 <skill>/scripts/mtgx.py add output.mtgx '{"type": "maltego.Person", "value": "Name"}'
python3 <skill>/scripts/mtgx.py remove output.mtgx n1
python3 <skill>/scripts/mtgx.py update output.mtgx n1 '{"person.nationality": "Thai"}'
python3 <skill>/scripts/mtgx.py embed output.mtgx n1 image.jpg
```

## JSON Input

```json
{
  "entities": [
    {
      "type": "maltego.Person",
      "value": "Name",
      "x": 100,
      "y": 100,
      "properties": {
        "person.fullname": "Name",
        "person.nationality": "Thai"
      }
    }
  ],
  "links": [
    {
      "src": "n1",
      "dst": "n2",
      "label": "Works at",
      "description": "Relationship details",
      "unverified": false
    }
  ],
  "logos": {
    "n1": "logos/image.jpg"
  },
  "logo_dir": "."
}
```

IDs are optional for entities. When omitted, entities are assigned sequential IDs `n1`, `n2`, and so on. Links must refer to existing entity IDs.

## NDJSON Input

One JSON object per line:

```json
{"type": "maltego.Person", "value": "Name"}
{"type": "maltego.Organization", "value": "Org"}
{"src": "n1", "dst": "n2", "label": "Works at"}
```

## Filters

```bash
--filter "type=maltego.Person"
--filter "type=maltego.Person,person.nationality=Thai"
--filter "type=maltego.Person,person.nationality!=Thai"
--filter "value~=Mauer"
```

Supported operators are exact match `=`, negation `!=`, and regex `~=`.

## Standard Properties

| Entity type | Property names |
| --- | --- |
| Person | `person.fullname`, `person.firstnames`, `person.lastname`, `person.nationality`, `person.age`, `person.status`, `person.position`, `person.alias` |
| Organization | `organization.name`, `title`, `country`, `status`, `organization.website` |
| Location | `location.name`, `title`, `location.country`, `location.city`, `location.area` |
| Document/Event | `title`, `description`, `date`, `url` |

## Validation Expectations

`validate` exits non-zero for dangling links, duplicate IDs, empty entity values, malformed ZIP files, missing required archive entries, or archive entries beyond the two-file MTGX invariant.
