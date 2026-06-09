#!/usr/bin/env python3
"""Validate a TOML file using Python 3.11+ tomllib.

Exit code 0 = valid, 1 = invalid.

Usage:
  python3 validate-toml.py file.toml
"""
import sys
import tomllib

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: validate-toml.py <file.toml>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path, "rb") as f:
            tomllib.load(f)
        print(f"{path}: valid")
    except Exception as e:
        print(f"{path}: invalid — {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
