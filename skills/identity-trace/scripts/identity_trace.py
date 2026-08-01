#!/usr/bin/env python3
"""Collect public identifier traces into a private, verifiable case bundle."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = "1.0"
USER_AGENT = "identity-trace-agent-skill"
MAX_INGEST_BYTES = 5 * 1024 * 1024
SOURCES = ("holehe", "maigret", "phoneinfoga", "github", "gravatar", "hibp")
TOOL_SOURCES = {
    "holehe": "holehe",
    "maigret": "maigret",
    "phoneinfoga": "phoneinfoga",
    "github": "gh",
}
SOURCE_TYPES = {
    "holehe": {"email"},
    "maigret": {"username"},
    "phoneinfoga": {"phone"},
    "github": {"email", "name", "username"},
    "gravatar": {"email"},
    "hibp": {"email"},
}
VALID_INPUT_TYPES = {"email", "phone", "username", "name", "birth_date"}
VALID_STATUSES = {"found", "not_found", "unknown", "skipped", "error"}
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^\+?[\d\s().-]{7,}$")
URL_RE = re.compile(r"https?://[^\s<>\]\[\)\(\"']+")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def utc_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def clean_text(value: Any, limit: int = 10_000) -> str:
    text = CONTROL_RE.sub("", str(value))
    return text[:limit]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(prefix: str, value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return f"{prefix}-{sha256_bytes(encoded)[:16]}"


def chmod_private(path: Path, directory: bool = False) -> None:
    if os.name == "posix":
        path.chmod(0o700 if directory else 0o600)


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    chmod_private(path, directory=True)


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temp.open("wb") as handle:
        handle.write(data)
    chmod_private(temp)
    temp.replace(path)
    chmod_private(path)


def write_text(path: Path, value: str) -> None:
    write_bytes(path, value.encode("utf-8"))


def write_json(path: Path, value: Any) -> None:
    write_text(
        path, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_input(kind: str, value: str) -> str:
    value = clean_text(value).strip()
    if not value:
        raise ValueError(f"empty {kind} input")
    if kind == "email":
        normalized = value.lower()
        if not EMAIL_RE.fullmatch(normalized):
            raise ValueError(f"invalid email address: {value}")
        return normalized
    if kind == "phone":
        digits = re.sub(r"\D", "", value)
        if not 7 <= len(digits) <= 15:
            raise ValueError(f"invalid phone number: {value}")
        return f"+{digits}"
    if kind == "username":
        normalized = value.removeprefix("@").strip()
        if not normalized or any(character.isspace() for character in normalized):
            raise ValueError(f"invalid username: {value}")
        return normalized
    if kind == "name":
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError(f"invalid name: {value}")
        return normalized
    if kind == "birth_date":
        if re.fullmatch(r"\d{4}", value):
            year = int(value)
            if not 1900 <= year <= dt.datetime.now().year:
                raise ValueError(f"invalid birth year: {value}")
            return value
        try:
            parsed = dt.date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                f"birth date must be YYYY or YYYY-MM-DD: {value}"
            ) from error
        if parsed > dt.date.today() or parsed.year < 1900:
            raise ValueError(f"invalid birth date: {value}")
        return parsed.isoformat()
    raise ValueError(f"unsupported input type: {kind}")


def detect_type(value: str) -> str:
    stripped = value.strip()
    if EMAIL_RE.fullmatch(stripped):
        return "email"
    if PHONE_RE.fullmatch(stripped):
        return "phone"
    if any(character.isspace() for character in stripped):
        return "name"
    return "username"


def build_inputs(args: argparse.Namespace) -> list[dict[str, str]]:
    candidates: list[tuple[str, str]] = []
    if args.target:
        candidates.append(
            (
                detect_type(args.target) if args.type == "auto" else args.type,
                args.target,
            )
        )
    for kind, attribute in (
        ("email", "emails"),
        ("phone", "phones"),
        ("username", "usernames"),
        ("name", "names"),
    ):
        candidates.extend((kind, value) for value in getattr(args, attribute))
    if args.birth_date:
        candidates.append(("birth_date", args.birth_date))
    if not candidates:
        raise ValueError("provide TARGET or at least one typed identifier")
    if all(kind == "birth_date" for kind, _ in candidates):
        raise ValueError("birth date requires at least one other identifier")

    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for kind, value in candidates:
        normalized = normalize_input(kind, value)
        key = (kind, normalized)
        if key in seen:
            continue
        seen.add(key)
        result.append(
            {
                "id": f"input-{len(result) + 1}",
                "type": kind,
                "value": clean_text(value),
                "normalized_value": normalized,
            }
        )
    return result


def tool_version(source: str) -> str | None:
    package_names = {"holehe": "holehe", "maigret": "maigret"}
    package = package_names.get(source)
    if not package:
        return None
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def doctor_data() -> dict[str, Any]:
    tools = {
        source: {
            "executable": executable,
            "path": shutil.which(executable),
            "available": shutil.which(executable) is not None,
        }
        for source, executable in TOOL_SOURCES.items()
    }
    return {
        "tools": tools,
        "credentials": {
            "HIBP_API_KEY": {"present": bool(os.environ.get("HIBP_API_KEY"))}
        },
        "http_sources": {
            "gravatar": {"available": True},
            "hibp": {"available": bool(os.environ.get("HIBP_API_KEY"))},
        },
    }


def parse_sources(include: str | None, exclude: str | None) -> list[str]:
    selected = set(
        SOURCES
        if not include
        else [item.strip() for item in include.split(",") if item.strip()]
    )
    removed = {item.strip() for item in (exclude or "").split(",") if item.strip()}
    unknown = (selected | removed) - set(SOURCES)
    if unknown:
        raise ValueError(f"unknown source(s): {', '.join(sorted(unknown))}")
    return [source for source in SOURCES if source in selected - removed]


def command_display(command: list[str]) -> list[str]:
    return [clean_text(part, 1_000) for part in command]


def run_process(
    command: list[str], cwd: Path, timeout: int
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def http_fetch(
    request: urllib.request.Request, timeout: int
) -> tuple[int, dict[str, str], bytes]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()


def raw_artifact(
    case_dir: Path, run_id: str, suffix: str, data: bytes
) -> dict[str, str]:
    relative = Path("raw") / f"{run_id}.{suffix.lstrip('.')}"
    write_bytes(case_dir / relative, data)
    return {"path": relative.as_posix(), "sha256": sha256_bytes(data)}


def new_run(
    source: str, input_record: dict[str, str], destination: str
) -> dict[str, Any]:
    return {
        "id": f"run-{uuid.uuid4().hex[:12]}",
        "source": source,
        "input_ids": [input_record["id"]],
        "status": "unknown",
        "destination": destination,
        "started_at": utc_now(),
        "completed_at": None,
        "command": [],
        "tool_version": tool_version(source),
        "error": None,
        "raw_artifacts": [],
    }


def observation(
    input_record: dict[str, str],
    source: str,
    status: str,
    kind: str,
    value: str = "",
    url: str = "",
    attributes: dict[str, Any] | None = None,
    raw_path: str | None = None,
) -> dict[str, Any]:
    identity = {
        "input_ids": [input_record["id"]],
        "source": source,
        "status": status,
        "kind": kind,
        "value": value,
        "url": url,
        "attributes": attributes or {},
    }
    return {
        "id": stable_id("obs", identity),
        **identity,
        "collected_at": utc_now(),
        "raw_artifact": raw_path,
    }


def unavailable_run(
    source: str, input_record: dict[str, str], destination: str, reason: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    run = new_run(source, input_record, destination)
    run.update(status="skipped", completed_at=utc_now(), error=reason)
    return run, []


def subprocess_adapter(
    source: str,
    input_record: dict[str, str],
    case_dir: Path,
    timeout: int,
    command_builder: Callable[[str, Path], list[str]],
    parser: Callable[[bytes, Path, str, dict[str, str]], list[dict[str, Any]]],
    destination: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    executable = TOOL_SOURCES[source]
    if not shutil.which(executable):
        return unavailable_run(
            source, input_record, destination, f"{executable} executable not found"
        )
    run = new_run(source, input_record, destination)
    with tempfile.TemporaryDirectory(prefix=f"identity-trace-{source}-") as temp_name:
        temp_dir = Path(temp_name)
        command = command_builder(input_record["normalized_value"], temp_dir)
        run["command"] = command_display(command)
        try:
            completed = run_process(command, temp_dir, timeout)
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or b""
            stderr = error.stderr or b""
            if stdout:
                run["raw_artifacts"].append(
                    raw_artifact(case_dir, run["id"], "stdout.txt", stdout)
                )
            if stderr:
                run["raw_artifacts"].append(
                    raw_artifact(case_dir, run["id"], "stderr.txt", stderr)
                )
            run.update(
                status="error",
                completed_at=utc_now(),
                error=f"timed out after {timeout} seconds",
            )
            return run, []
        if completed.stdout:
            run["raw_artifacts"].append(
                raw_artifact(case_dir, run["id"], "stdout.txt", completed.stdout)
            )
        if completed.stderr:
            run["raw_artifacts"].append(
                raw_artifact(case_dir, run["id"], "stderr.txt", completed.stderr)
            )
        try:
            observations = parser(completed.stdout, temp_dir, run["id"], input_record)
            for artifact_index, artifact_path in enumerate(
                sorted(temp_dir.rglob("*")), start=1
            ):
                if not artifact_path.is_file():
                    continue
                data = artifact_path.read_bytes()
                suffix = f"output-{artifact_index}" + (artifact_path.suffix or ".bin")
                artifact = raw_artifact(case_dir, run["id"], suffix, data)
                if artifact not in run["raw_artifacts"]:
                    run["raw_artifacts"].append(artifact)
                for item in observations:
                    if item["raw_artifact"] is None:
                        item["raw_artifact"] = artifact["path"]
            if completed.returncode != 0 and not observations:
                run.update(
                    status="error",
                    error=f"process exited with status {completed.returncode}",
                )
            else:
                if any(item["status"] == "found" for item in observations):
                    run["status"] = "found"
                elif observations or source in {"holehe", "maigret"}:
                    run["status"] = "not_found"
                else:
                    run["status"] = "unknown"
            run["completed_at"] = utc_now()
            return run, observations
        except (ValueError, json.JSONDecodeError, csv.Error) as error:
            run.update(
                status="error",
                completed_at=utc_now(),
                error=f"could not parse output: {error}",
            )
            return run, []


def parse_holehe(
    _: bytes, temp_dir: Path, __: str, input_record: dict[str, str]
) -> list[dict[str, Any]]:
    csv_files = sorted(temp_dir.rglob("*.csv"))
    if not csv_files:
        return []
    results: list[dict[str, Any]] = []
    with csv_files[0].open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            exists = str(row.get("exists", "")).strip().lower()
            if exists not in {"true", "false"}:
                continue
            status = "found" if exists == "true" else "not_found"
            domain = clean_text(row.get("domain") or row.get("name") or "")
            attributes = {
                clean_text(key): clean_text(value)
                for key, value in row.items()
                if key and value not in (None, "")
            }
            results.append(
                observation(
                    input_record,
                    "holehe",
                    status,
                    "account-registration",
                    domain,
                    attributes=attributes,
                )
            )
    return results


def parse_maigret(
    stdout: bytes, temp_dir: Path, _: str, input_record: dict[str, str]
) -> list[dict[str, Any]]:
    blobs = [stdout] + [
        path.read_bytes()
        for path in sorted(temp_dir.rglob("*.json"))
        + sorted(temp_dir.rglob("*.ndjson"))
    ]
    records: list[dict[str, Any]] = []
    for blob in blobs:
        text = blob.decode("utf-8", errors="replace").strip()
        if not text:
            continue
        try:
            value = json.loads(text)
            if isinstance(value, dict):
                records.extend(
                    value.values()
                    if all(isinstance(item, dict) for item in value.values())
                    else [value]
                )
            elif isinstance(value, list):
                records.extend(item for item in value if isinstance(item, dict))
            continue
        except json.JSONDecodeError:
            pass
        for line in text.splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
    results: list[dict[str, Any]] = []
    for record in records:
        url = clean_text(
            record.get("url_user") or record.get("url") or record.get("link") or ""
        )
        status_text = str(
            record.get("status")
            or record.get("status_enum")
            or record.get("exists")
            or ""
        ).lower()
        is_found = status_text in {"true", "claimed", "found", "exists"} or bool(
            record.get("is_found")
        )
        is_not_found = status_text in {
            "false",
            "available",
            "not_found",
            "not found",
            "unclaimed",
        }
        if not url and not is_found:
            continue
        status = "found" if is_found else "not_found" if is_not_found else "unknown"
        results.append(
            observation(
                input_record,
                "maigret",
                status,
                "profile",
                url=url,
                value=clean_text(record.get("site_name") or record.get("site") or ""),
                attributes=record,
            )
        )
    return results


def parse_phoneinfoga(
    stdout: bytes, _: Path, __: str, input_record: dict[str, str]
) -> list[dict[str, Any]]:
    text = stdout.decode("utf-8", errors="replace")
    urls = sorted(set(URL_RE.findall(text)))
    return [
        observation(input_record, "phoneinfoga", "found", "reference-url", url=url)
        for url in urls
    ]


def parse_json_stdout(stdout: bytes) -> Any:
    if not stdout.strip():
        return None
    return json.loads(stdout.decode("utf-8"))


def github_adapter(
    input_record: dict[str, str], case_dir: Path, timeout: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not shutil.which("gh"):
        return unavailable_run(
            "github", input_record, "api.github.com", "gh executable not found"
        )
    value = input_record["normalized_value"]
    kind = input_record["type"]
    if kind == "username":
        command = ["gh", "api", f"users/{urllib.parse.quote(value, safe='')}"]
    else:
        qualifier = "--author-email" if kind == "email" else "--author-name"
        command = [
            "gh",
            "search",
            "commits",
            qualifier,
            value,
            "--limit",
            "30",
            "--json",
            "author,commit,repository,sha,url",
        ]
    run = new_run("github", input_record, "api.github.com")
    run["command"] = command_display(command)
    try:
        completed = run_process(command, Path.cwd(), timeout)
    except subprocess.TimeoutExpired:
        run.update(
            status="error",
            completed_at=utc_now(),
            error=f"timed out after {timeout} seconds",
        )
        return run, []
    artifact = raw_artifact(case_dir, run["id"], "json", completed.stdout or b"null\n")
    run["raw_artifacts"].append(artifact)
    if completed.stderr:
        run["raw_artifacts"].append(
            raw_artifact(case_dir, run["id"], "stderr.txt", completed.stderr)
        )
    if completed.returncode != 0:
        run.update(
            status="error",
            completed_at=utc_now(),
            error=f"gh exited with status {completed.returncode}",
        )
        return run, []
    try:
        data = parse_json_stdout(completed.stdout)
    except json.JSONDecodeError as error:
        run.update(
            status="error",
            completed_at=utc_now(),
            error=f"could not parse output: {error}",
        )
        return run, []
    observations: list[dict[str, Any]] = []
    if kind == "username" and isinstance(data, dict):
        url = clean_text(data.get("html_url") or "")
        observations.append(
            observation(
                input_record,
                "github",
                "found",
                "profile",
                clean_text(data.get("login") or value),
                url,
                data,
                artifact["path"],
            )
        )
    elif isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            observations.append(
                observation(
                    input_record,
                    "github",
                    "found",
                    "commit",
                    clean_text(item.get("sha") or ""),
                    clean_text(item.get("url") or ""),
                    item,
                    artifact["path"],
                )
            )
    run.update(status="found" if observations else "not_found", completed_at=utc_now())
    return run, observations


def http_adapter(
    input_record: dict[str, str], case_dir: Path, timeout: int, source: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    value = input_record["normalized_value"]
    if source == "gravatar":
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        url = f"https://gravatar.com/avatar/{digest}?s=64&d=404"
        headers = {"User-Agent": USER_AGENT}
        destination = "gravatar.com"
    else:
        api_key = os.environ.get("HIBP_API_KEY")
        if not api_key:
            return unavailable_run(
                "hibp", input_record, "haveibeenpwned.com", "HIBP_API_KEY is not set"
            )
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(value, safe='')}?truncateResponse=false"
        headers = {"User-Agent": USER_AGENT, "hibp-api-key": api_key}
        destination = "haveibeenpwned.com"
    run = new_run(source, input_record, destination)
    run["command"] = ["GET", url]
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        status_code, response_headers, body = http_fetch(request, timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        run.update(status="error", completed_at=utc_now(), error=clean_text(error))
        return run, []
    suffix = "image" if source == "gravatar" and status_code == 200 else "json"
    artifact = raw_artifact(case_dir, run["id"], suffix, body)
    run["raw_artifacts"].append(artifact)
    safe_headers = {
        key.lower(): clean_text(value)
        for key, value in response_headers.items()
        if key.lower() in {"content-type", "etag", "last-modified", "retry-after"}
    }
    observations: list[dict[str, Any]] = []
    if status_code == 404:
        observations.append(
            observation(
                input_record,
                source,
                "not_found",
                "avatar" if source == "gravatar" else "breach",
                attributes={"http_status": 404},
                raw_path=artifact["path"],
            )
        )
        run["status"] = "not_found"
    elif status_code == 200 and source == "gravatar":
        observations.append(
            observation(
                input_record,
                source,
                "found",
                "avatar",
                url=url,
                attributes={"http_status": 200, "headers": safe_headers},
                raw_path=artifact["path"],
            )
        )
        run["status"] = "found"
    elif status_code == 200:
        try:
            breaches = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            run.update(
                status="error",
                completed_at=utc_now(),
                error=f"invalid HIBP JSON: {error}",
            )
            return run, []
        for breach in breaches if isinstance(breaches, list) else []:
            if isinstance(breach, dict):
                domain = clean_text(breach.get("Domain") or "")
                breach_url = f"https://{domain}" if domain else ""
                observations.append(
                    observation(
                        input_record,
                        source,
                        "found",
                        "breach",
                        clean_text(breach.get("Name") or breach.get("Title") or ""),
                        breach_url,
                        breach,
                        artifact["path"],
                    )
                )
        run["status"] = "found" if observations else "not_found"
    else:
        run.update(
            status="error",
            error=f"HTTP {status_code}"
            + (
                f"; retry after {safe_headers['retry-after']}"
                if safe_headers.get("retry-after")
                else ""
            ),
        )
    run["completed_at"] = utc_now()
    return run, observations


def execute_source(
    source: str, input_record: dict[str, str], case_dir: Path, timeout: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if source == "holehe":
        return subprocess_adapter(
            source,
            input_record,
            case_dir,
            timeout,
            lambda value, _: [
                "holehe",
                value,
                "--no-color",
                "--no-clear",
                "-C",
                "-T",
                str(timeout),
            ],
            parse_holehe,
            "service domains queried by Holehe",
        )
    if source == "maigret":
        return subprocess_adapter(
            source,
            input_record,
            case_dir,
            timeout,
            lambda value, temp: [
                "maigret",
                value,
                "--json",
                "ndjson",
                "-fo",
                str(temp),
                "--no-color",
            ],
            parse_maigret,
            "profile sites queried by Maigret",
        )
    if source == "phoneinfoga":
        return subprocess_adapter(
            source,
            input_record,
            case_dir,
            timeout,
            lambda value, _: ["phoneinfoga", "scan", "-n", value],
            parse_phoneinfoga,
            "sources queried by PhoneInfoga",
        )
    if source == "github":
        return github_adapter(input_record, case_dir, timeout)
    if source in {"gravatar", "hibp"}:
        return http_adapter(input_record, case_dir, timeout, source)
    raise ValueError(f"unsupported source: {source}")


def build_queries(inputs: list[dict[str, str]]) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    birth_dates = [item for item in inputs if item["type"] == "birth_date"]
    for item in inputs:
        if item["type"] == "birth_date":
            continue
        value = item["normalized_value"]
        values: list[str] = [f'"{value}"']
        if item["type"] == "username":
            values.extend(
                [
                    f'site:github.com "{value}"',
                    f'site:reddit.com "{value}"',
                    f'site:instagram.com "{value}"',
                ]
            )
        elif item["type"] == "email":
            values.append(f'"{value.split("@", 1)[0]}"')
        elif item["type"] == "phone":
            values.append(f'"{value.removeprefix("+")}"')
        elif item["type"] == "name":
            values.extend(
                f'"{value}" "{birth["normalized_value"]}"' for birth in birth_dates
            )
            values.extend(
                [f'site:linkedin.com/in "{value}"', f'site:github.com "{value}"']
            )
        for query in values:
            related = [item["id"]]
            related.extend(
                birth["id"]
                for birth in birth_dates
                if birth["normalized_value"] in query
            )
            record = {"input_ids": related, "query": query, "status": "planned"}
            record["id"] = stable_id("query", record)
            queries.append(record)
    return queries


def derive_relationships(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relationships = []
    for item in observations:
        parsed = urllib.parse.urlparse(str(item.get("url") or ""))
        if (
            item.get("status") != "found"
            or parsed.scheme not in {"http", "https"}
            or not parsed.netloc
        ):
            continue
        for input_id in item.get("input_ids", []):
            relationships.append(
                {
                    "from": input_id,
                    "to": item["url"],
                    "type": "identifier_resolves_to_resource",
                    "source_observation_ids": [item["id"]],
                }
            )
    return relationships


def summarize(case: dict[str, Any]) -> dict[str, Any]:
    run_counts = {status: 0 for status in VALID_STATUSES}
    observation_counts = {status: 0 for status in VALID_STATUSES}
    for run in case["runs"]:
        run_counts[run["status"]] = run_counts.get(run["status"], 0) + 1
    for item in case["observations"]:
        observation_counts[item["status"]] = (
            observation_counts.get(item["status"], 0) + 1
        )
    return {
        "inputs": len(case["inputs"]),
        "runs": run_counts,
        "observations": observation_counts,
    }


def md_cell(value: Any) -> str:
    return clean_text(value).replace("|", "\\|").replace("\n", " ") or "—"


def render_report(case: dict[str, Any]) -> str:
    lines = [
        f"# Identity Trace {case['case_id']}",
        "",
        f"Collected: {case['started_at']} to {case['completed_at']}",
        "",
        "## Collection Configuration",
        "",
        f"- Selected sources: {', '.join(case['configuration']['selected_sources']) or 'none'}",
        f"- Excluded sources: {', '.join(case['configuration']['excluded_sources']) or 'none'}",
        f"- Timeout: {case['configuration']['timeout_seconds']} seconds",
        "",
        "## Inputs",
        "",
        "| ID | Type | Value | Normalized |",
        "| --- | --- | --- | --- |",
    ]
    for item in case["inputs"]:
        lines.append(
            f"| {md_cell(item['id'])} | {md_cell(item['type'])} | {md_cell(item['value'])} | {md_cell(item['normalized_value'])} |"
        )
    lines.extend(
        [
            "",
            "## Source Coverage",
            "",
            "| Source | Inputs | Status | Destination | Error |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for run in case["runs"]:
        lines.append(
            f"| {md_cell(run['source'])} | {md_cell(', '.join(run['input_ids']))} | {md_cell(run['status'])} | {md_cell(run['destination'])} | {md_cell(run.get('error'))} |"
        )
    lines.extend(
        [
            "",
            "## Observations",
            "",
            "| Source | Status | Kind | Value | URL | Evidence |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in case["observations"]:
        lines.append(
            f"| {md_cell(item['source'])} | {md_cell(item['status'])} | {md_cell(item['kind'])} | {md_cell(item.get('value'))} | {md_cell(item.get('url'))} | {md_cell(item.get('raw_artifact'))} |"
        )
    lines.extend(["", "## Search Pivots", ""])
    for query in case["queries"]:
        lines.append(
            f"- `{query['query']}` ({query['status']}; {', '.join(query['input_ids'])})"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "This report records source-specific observations. It does not assert that separate accounts or resources belong to the same person.",
            "",
        ]
    )
    return "\n".join(lines)


def manifest_entries(case_dir: Path) -> list[tuple[str, str]]:
    entries = []
    for path in sorted(case_dir.rglob("*")):
        if (
            path.is_file()
            and not path.is_symlink()
            and path.name != "SHA256SUMS"
            and not path.name.startswith(".")
        ):
            entries.append(
                (sha256_bytes(path.read_bytes()), path.relative_to(case_dir).as_posix())
            )
    return entries


def write_manifest(case_dir: Path) -> None:
    write_text(
        case_dir / "SHA256SUMS",
        "".join(f"{digest}  {path}\n" for digest, path in manifest_entries(case_dir)),
    )


def write_case_bundle(case_dir: Path, case: dict[str, Any]) -> None:
    case["relationships"] = derive_relationships(case["observations"])
    case["summary"] = summarize(case)
    write_json(case_dir / "case.json", case)
    write_json(case_dir / "queries.json", case["queries"])
    write_text(case_dir / "report.md", render_report(case))
    write_manifest(case_dir)


def default_case_dir() -> Path:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path.cwd() / "identity-traces" / f"{timestamp}-{uuid.uuid4().hex[:8]}"


def run_command(args: argparse.Namespace) -> int:
    inputs = build_inputs(args)
    selected = parse_sources(args.sources, args.exclude)
    case_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else default_case_dir().resolve()
    )
    if case_dir.exists() and any(case_dir.iterdir()):
        raise ValueError(f"output directory is not empty: {case_dir}")
    ensure_private_dir(case_dir)
    ensure_private_dir(case_dir / "raw")
    case: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": uuid.uuid4().hex[:12],
        "started_at": utc_now(),
        "completed_at": None,
        "configuration": {
            "selected_sources": selected,
            "excluded_sources": sorted(set(SOURCES) - set(selected)),
            "timeout_seconds": args.timeout,
        },
        "inputs": inputs,
        "runs": [],
        "observations": [],
        "relationships": [],
        "queries": build_queries(inputs),
        "summary": {},
    }
    for source in selected:
        applicable = [item for item in inputs if item["type"] in SOURCE_TYPES[source]]
        for item in applicable:
            print(f"identity-trace: {source} for {item['id']}", file=sys.stderr)
            run, observations = execute_source(source, item, case_dir, args.timeout)
            case["runs"].append(run)
            case["observations"].extend(observations)
    case["completed_at"] = utc_now()
    write_case_bundle(case_dir, case)
    print(
        json.dumps(
            {
                "case_dir": str(case_dir),
                "case_id": case["case_id"],
                "summary": case["summary"],
            },
            sort_keys=True,
        )
    )
    return 0


def load_ingest_payload(path_value: str) -> Any:
    if path_value == "-":
        data = sys.stdin.buffer.read(MAX_INGEST_BYTES + 1)
    else:
        path = Path(path_value)
        if path.stat().st_size > MAX_INGEST_BYTES:
            raise ValueError("ingest input exceeds 5 MB")
        data = path.read_bytes()
    if len(data) > MAX_INGEST_BYTES:
        raise ValueError("ingest input exceeds 5 MB")
    return json.loads(data.decode("utf-8"))


def ingest_command(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).expanduser().resolve()
    case = read_json(case_dir / "case.json")
    payload = load_ingest_payload(args.input)
    records = payload if isinstance(payload, list) else [payload]
    input_ids = {item["id"] for item in case.get("inputs", [])}
    existing = {item["id"] for item in case.get("observations", [])}
    added = 0
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each ingest record must be an object")
        related = record.get("input_ids")
        if (
            not isinstance(related, list)
            or not related
            or not all(item in input_ids for item in related)
        ):
            raise ValueError("ingest input_ids must reference existing case inputs")
        url = clean_text(record.get("url", ""))
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("ingest url must be an absolute HTTP(S) URL")
        identity = {
            "input_ids": sorted(set(related)),
            "source": clean_text(record.get("source") or "web"),
            "status": "found",
            "kind": "web-result",
            "value": clean_text(record.get("title", "")),
            "url": url,
            "attributes": {
                "query": clean_text(record.get("query", "")),
                "title": clean_text(record.get("title", "")),
                "snippet": clean_text(record.get("snippet", "")),
            },
        }
        item = {
            "id": stable_id("obs", identity),
            **identity,
            "collected_at": clean_text(record.get("observed_at") or utc_now()),
            "raw_artifact": None,
        }
        if item["id"] not in existing:
            case["observations"].append(item)
            existing.add(item["id"])
            added += 1
        for query in case.get("queries", []):
            if query["query"] == identity["attributes"]["query"] and set(
                query["input_ids"]
            ) == set(identity["input_ids"]):
                query["status"] = "executed"
    case["completed_at"] = utc_now()
    write_case_bundle(case_dir, case)
    print(
        json.dumps(
            {
                "case_dir": str(case_dir),
                "added": added,
                "total_observations": len(case["observations"]),
            },
            sort_keys=True,
        )
    )
    return 0


def validate_case(case_dir: Path) -> list[str]:
    errors: list[str] = []
    required_files = ("case.json", "report.md", "queries.json", "SHA256SUMS")
    for name in required_files:
        if not (case_dir / name).is_file():
            errors.append(f"missing {name}")
    if errors:
        return errors
    for path in case_dir.rglob("*"):
        if path.is_symlink():
            errors.append(
                f"symbolic links are not allowed: {path.relative_to(case_dir)}"
            )
    try:
        case = read_json(case_dir / "case.json")
    except (OSError, json.JSONDecodeError) as error:
        return [f"invalid case.json: {error}"]
    required_fields = {
        "schema_version",
        "case_id",
        "started_at",
        "completed_at",
        "configuration",
        "inputs",
        "runs",
        "observations",
        "relationships",
        "queries",
        "summary",
    }
    missing = required_fields - set(case) if isinstance(case, dict) else required_fields
    if missing:
        errors.append(f"case.json missing fields: {', '.join(sorted(missing))}")
    if case.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version: {case.get('schema_version')}")
    ids: list[str] = []
    for group in ("inputs", "runs", "observations", "queries"):
        records = case.get(group, [])
        if not isinstance(records, list):
            errors.append(f"{group} must be an array")
            continue
        for record in records:
            if not isinstance(record, dict) or not record.get("id"):
                errors.append(f"{group} contains a record without an id")
            else:
                ids.append(record["id"])
    if len(ids) != len(set(ids)):
        errors.append("duplicate record id")
    for item in case.get("inputs", []):
        if item.get("type") not in VALID_INPUT_TYPES:
            errors.append(f"invalid input type: {item.get('type')}")
    for group in ("runs", "observations"):
        for item in case.get(group, []):
            if item.get("status") not in VALID_STATUSES:
                errors.append(f"invalid {group} status: {item.get('status')}")
    for run in case.get("runs", []):
        for artifact in run.get("raw_artifacts", []):
            relative = Path(str(artifact.get("path", "")))
            target = (case_dir / relative).resolve()
            if case_dir not in target.parents or not target.is_file():
                errors.append(f"missing or unsafe raw artifact: {relative}")
            elif sha256_bytes(target.read_bytes()) != artifact.get("sha256"):
                errors.append(f"raw artifact hash mismatch: {relative}")
    expected = {path: digest for digest, path in manifest_entries(case_dir)}
    actual: dict[str, str] = {}
    for line in (case_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, separator, path = line.partition("  ")
        if not separator:
            errors.append(f"invalid manifest line: {line}")
            continue
        actual[path] = digest
    if actual != expected:
        errors.append("SHA256SUMS does not match bundle contents")
    return errors


def validate_command(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).expanduser().resolve()
    errors = validate_case(case_dir)
    result = {"case_dir": str(case_dir), "valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print(f"Valid identity-trace bundle: {case_dir}")
    return 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command_name", required=True)
    doctor = subparsers.add_parser(
        "doctor", help="inspect optional source availability without invoking tools"
    )
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(
        handler=lambda args: (
            print(
                json.dumps(
                    doctor_data(), indent=2 if args.json else None, sort_keys=True
                )
            )
            or 0
        )
    )

    run = subparsers.add_parser(
        "run", help="collect traces and write a private case bundle"
    )
    run.add_argument("target", nargs="?")
    run.add_argument(
        "--type", choices=("auto", "email", "phone", "username", "name"), default="auto"
    )
    run.add_argument("--email", dest="emails", action="append", default=[])
    run.add_argument("--phone", dest="phones", action="append", default=[])
    run.add_argument("--username", dest="usernames", action="append", default=[])
    run.add_argument("--name", dest="names", action="append", default=[])
    run.add_argument("--birth-date")
    run.add_argument("--sources")
    run.add_argument("--exclude")
    run.add_argument("--output")
    run.add_argument("--timeout", type=int, default=30)
    run.set_defaults(handler=run_command)

    ingest = subparsers.add_parser(
        "ingest", help="add selected web results and regenerate derived artifacts"
    )
    ingest.add_argument("case_dir")
    ingest.add_argument("--input", required=True)
    ingest.set_defaults(handler=ingest_command)

    validate = subparsers.add_parser(
        "validate", help="validate schema, artifacts, and manifest"
    )
    validate.add_argument("case_dir")
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(handler=validate_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "timeout", 1) < 1:
        parser.error("--timeout must be at least 1 second")
    try:
        return int(args.handler(args))
    except ValueError as error:
        print(f"identity-trace: {error}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as error:
        print(f"identity-trace: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
