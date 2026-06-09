#!/usr/bin/env python3
"""Append a value to a JSON array from stdin, output to stdout.

Designed for piping: toml-get emits JSON arrays, toml-set accepts them.

Usage:
  toml get file.toml dns.hosts | python3 append-toml-array.py "new entry" | toml set file.toml dns.hosts
"""
import json
import sys

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: append-toml-array.py <value> [value...]", file=sys.stderr)
        sys.exit(1)

    values = sys.argv[1:]

    try:
        arr = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"error: stdin is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(arr, list):
        print(f"error: stdin must be a JSON array, got {type(arr).__name__}", file=sys.stderr)
        sys.exit(1)

    for v in values:
        arr.append(v)

    json.dump(arr, sys.stdout)
    print()

if __name__ == "__main__":
    main()
