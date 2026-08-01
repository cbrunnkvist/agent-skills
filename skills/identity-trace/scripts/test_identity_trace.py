#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("identity_trace.py")
SPEC = importlib.util.spec_from_file_location("identity_trace", MODULE_PATH)
assert SPEC and SPEC.loader
identity_trace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(identity_trace)


def input_record(kind: str, value: str) -> dict[str, str]:
    return {"id": "input-1", "type": kind, "value": value, "normalized_value": value}


class InputTests(unittest.TestCase):
    def test_detect_and_normalize(self) -> None:
        self.assertEqual(identity_trace.detect_type("User@Example.COM"), "email")
        self.assertEqual(identity_trace.detect_type("+1 (202) 555-0123"), "phone")
        self.assertEqual(identity_trace.detect_type("Jane Example"), "name")
        self.assertEqual(identity_trace.detect_type("unique_handle"), "username")
        self.assertEqual(
            identity_trace.normalize_input("email", " User@Example.COM "),
            "user@example.com",
        )
        self.assertEqual(
            identity_trace.normalize_input("phone", "+1 (202) 555-0123"), "+12025550123"
        )
        self.assertEqual(
            identity_trace.normalize_input("username", "@unique_handle"),
            "unique_handle",
        )
        self.assertEqual(
            identity_trace.normalize_input("name", " Jane   Example "), "Jane Example"
        )

    def test_birth_date_requires_another_identifier(self) -> None:
        args = argparse.Namespace(
            target=None,
            type="auto",
            emails=[],
            phones=[],
            usernames=[],
            names=[],
            birth_date="1988",
        )
        with self.assertRaisesRegex(ValueError, "requires"):
            identity_trace.build_inputs(args)

    def test_invalid_birth_date(self) -> None:
        with self.assertRaises(ValueError):
            identity_trace.normalize_input("birth_date", "1880")
        with self.assertRaises(ValueError):
            identity_trace.normalize_input("birth_date", "2000-13-40")

    def test_source_selection(self) -> None:
        self.assertEqual(
            identity_trace.parse_sources("github,gravatar", "gravatar"), ["github"]
        )
        with self.assertRaisesRegex(ValueError, "unknown"):
            identity_trace.parse_sources("sherlock", None)

    def test_name_birth_date_query_references_both_inputs(self) -> None:
        records = [
            {
                "id": "input-1",
                "type": "name",
                "value": "Jane Example",
                "normalized_value": "Jane Example",
            },
            {
                "id": "input-2",
                "type": "birth_date",
                "value": "1988",
                "normalized_value": "1988",
            },
        ]
        contextual = [
            item
            for item in identity_trace.build_queries(records)
            if "1988" in item["query"]
        ]
        self.assertEqual(contextual[0]["input_ids"], ["input-1", "input-2"])


class DoctorTests(unittest.TestCase):
    def test_doctor_never_invokes_a_tool(self) -> None:
        with (
            mock.patch.object(
                identity_trace.shutil, "which", return_value="/fake/tool"
            ),
            mock.patch.object(
                identity_trace.subprocess,
                "run",
                side_effect=AssertionError("must not execute"),
            ),
        ):
            result = identity_trace.doctor_data()
        self.assertTrue(result["tools"]["holehe"]["available"])


class ParserTests(unittest.TestCase):
    def test_holehe_csv_is_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "pii-named-upstream.csv"
            path.write_text(
                "name,domain,exists,rateLimit\nGitHub,github.com,true,false\nOther,other.test,false,false\n",
                encoding="utf-8",
            )
            results = identity_trace.parse_holehe(
                b"", Path(name), "run-1", input_record("email", "test@example.com")
            )
        self.assertEqual([item["status"] for item in results], ["found", "not_found"])

    def test_maigret_ndjson_is_parsed(self) -> None:
        data = b'{"site_name":"GitHub","url_user":"https://github.com/example","status":"CLAIMED"}\n'
        with tempfile.TemporaryDirectory() as name:
            results = identity_trace.parse_maigret(
                data, Path(name), "run-1", input_record("username", "example")
            )
        self.assertEqual(results[0]["url"], "https://github.com/example")
        self.assertEqual(results[0]["status"], "found")

    def test_phoneinfoga_only_promotes_urls(self) -> None:
        output = b"Country: Thailand\nSearch: https://example.test/phone?q=123\n"
        results = identity_trace.parse_phoneinfoga(
            output, Path("."), "run-1", input_record("phone", "+66123456789")
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["kind"], "reference-url")


class AdapterTests(unittest.TestCase):
    def test_holehe_nonzero_with_csv_is_evidence(self) -> None:
        def fake_process(
            command: list[str], cwd: Path, timeout: int
        ) -> subprocess.CompletedProcess[bytes]:
            (cwd / "raw-email-name.csv").write_text(
                "name,domain,exists\nGitHub,github.com,true\n", encoding="utf-8"
            )
            return subprocess.CompletedProcess(command, 1, b"exported", b"")

        with (
            tempfile.TemporaryDirectory() as name,
            mock.patch.object(
                identity_trace.shutil, "which", return_value="/fake/holehe"
            ),
            mock.patch.object(identity_trace, "run_process", side_effect=fake_process),
        ):
            case_dir = Path(name)
            identity_trace.ensure_private_dir(case_dir / "raw")
            run, observations = identity_trace.execute_source(
                "holehe", input_record("email", "test@example.com"), case_dir, 5
            )
            raw_names = [Path(item["path"]).name for item in run["raw_artifacts"]]
        self.assertEqual(run["status"], "found")
        self.assertEqual(len(observations), 1)
        self.assertNotIn("test@example.com", " ".join(raw_names))

    def test_phoneinfoga_empty_success_is_unknown(self) -> None:
        completed = subprocess.CompletedProcess(
            ["phoneinfoga"], 0, b"Country: Thailand\n", b""
        )
        with (
            tempfile.TemporaryDirectory() as name,
            mock.patch.object(
                identity_trace.shutil, "which", return_value="/fake/phoneinfoga"
            ),
            mock.patch.object(identity_trace, "run_process", return_value=completed),
        ):
            case_dir = Path(name)
            identity_trace.ensure_private_dir(case_dir / "raw")
            run, observations = identity_trace.execute_source(
                "phoneinfoga", input_record("phone", "+66123456789"), case_dir, 5
            )
        self.assertEqual(run["status"], "unknown")
        self.assertEqual(observations, [])

    def test_github_username(self) -> None:
        data = json.dumps(
            {"login": "example", "html_url": "https://github.com/example"}
        ).encode()
        completed = subprocess.CompletedProcess(["gh"], 0, data, b"")
        with (
            tempfile.TemporaryDirectory() as name,
            mock.patch.object(identity_trace.shutil, "which", return_value="/fake/gh"),
            mock.patch.object(identity_trace, "run_process", return_value=completed),
        ):
            case_dir = Path(name)
            identity_trace.ensure_private_dir(case_dir / "raw")
            run, observations = identity_trace.github_adapter(
                input_record("username", "example"), case_dir, 5
            )
        self.assertEqual(run["status"], "found")
        self.assertEqual(observations[0]["url"], "https://github.com/example")

    def test_gravatar_404(self) -> None:
        with (
            tempfile.TemporaryDirectory() as name,
            mock.patch.object(
                identity_trace,
                "http_fetch",
                return_value=(404, {"Content-Type": "application/json"}, b""),
            ),
        ):
            case_dir = Path(name)
            identity_trace.ensure_private_dir(case_dir / "raw")
            run, observations = identity_trace.http_adapter(
                input_record("email", "test@example.com"), case_dir, 5, "gravatar"
            )
        self.assertEqual(run["status"], "not_found")
        self.assertEqual(observations[0]["status"], "not_found")

    def test_hibp_found_and_rate_limit(self) -> None:
        breaches = json.dumps(
            [{"Name": "ExampleBreach", "Domain": "example.test"}]
        ).encode()
        with (
            tempfile.TemporaryDirectory() as name,
            mock.patch.dict(os.environ, {"HIBP_API_KEY": "secret"}),
            mock.patch.object(
                identity_trace, "http_fetch", return_value=(200, {}, breaches)
            ),
        ):
            case_dir = Path(name)
            identity_trace.ensure_private_dir(case_dir / "raw")
            run, observations = identity_trace.http_adapter(
                input_record("email", "test@example.com"), case_dir, 5, "hibp"
            )
        self.assertEqual(run["status"], "found")
        self.assertEqual(observations[0]["url"], "https://example.test")
        self.assertNotIn("secret", json.dumps(run))

        with (
            tempfile.TemporaryDirectory() as name,
            mock.patch.dict(os.environ, {"HIBP_API_KEY": "secret"}),
            mock.patch.object(
                identity_trace,
                "http_fetch",
                return_value=(429, {"Retry-After": "5"}, b"{}"),
            ),
        ):
            case_dir = Path(name)
            identity_trace.ensure_private_dir(case_dir / "raw")
            limited, _ = identity_trace.http_adapter(
                input_record("email", "test@example.com"), case_dir, 5, "hibp"
            )
        self.assertEqual(limited["status"], "error")
        self.assertIn("retry after 5", limited["error"])


class BundleTests(unittest.TestCase):
    def make_case(self, root: Path) -> Path:
        args = argparse.Namespace(
            target="test@example.com",
            type="auto",
            emails=[],
            phones=[],
            usernames=[],
            names=[],
            birth_date=None,
            sources=None,
            exclude=",".join(identity_trace.SOURCES),
            output=str(root / "case"),
            timeout=5,
        )
        with mock.patch("sys.stdout"):
            self.assertEqual(identity_trace.run_command(args), 0)
        return root / "case"

    def test_bundle_permissions_and_validation(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            case_dir = self.make_case(Path(name))
            self.assertEqual(identity_trace.validate_case(case_dir), [])
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(case_dir.stat().st_mode), 0o700)
                self.assertEqual(
                    stat.S_IMODE((case_dir / "case.json").stat().st_mode), 0o600
                )
            self.assertNotIn(
                "test@example.com",
                " ".join(
                    str(path.relative_to(case_dir)) for path in case_dir.rglob("*")
                ),
            )

    def test_ingest_is_idempotent_and_updates_query(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            case_dir = self.make_case(root)
            case = identity_trace.read_json(case_dir / "case.json")
            query = case["queries"][0]
            payload = [
                {
                    "input_ids": ["input-1"],
                    "source": "web",
                    "query": query["query"],
                    "url": "https://example.test/profile",
                    "title": "Example",
                    "snippet": "Public result",
                    "observed_at": "2026-08-01T00:00:00Z",
                }
            ]
            input_path = root / "ingest.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            args = argparse.Namespace(case_dir=str(case_dir), input=str(input_path))
            with mock.patch("sys.stdout"):
                identity_trace.ingest_command(args)
                identity_trace.ingest_command(args)
            updated = identity_trace.read_json(case_dir / "case.json")
            self.assertEqual(len(updated["observations"]), 1)
            self.assertEqual(updated["queries"][0]["status"], "executed")
            self.assertEqual(identity_trace.validate_case(case_dir), [])

    def test_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            case_dir = self.make_case(Path(name))
            (case_dir / "report.md").write_text("altered", encoding="utf-8")
            self.assertIn(
                "SHA256SUMS does not match bundle contents",
                identity_trace.validate_case(case_dir),
            )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            case_dir = self.make_case(root)
            os.symlink(case_dir / "case.json", case_dir / "raw" / "linked.json")
            identity_trace.write_manifest(case_dir)
            errors = identity_trace.validate_case(case_dir)
            self.assertTrue(any("symbolic links" in error for error in errors))

    def test_partial_failure_still_writes_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            args = argparse.Namespace(
                target="example_user",
                type="auto",
                emails=[],
                phones=[],
                usernames=[],
                names=[],
                birth_date=None,
                sources="maigret",
                exclude=None,
                output=str(root / "case"),
                timeout=5,
            )
            failed_run = identity_trace.new_run(
                "maigret", input_record("username", "example_user"), "profile sites"
            )
            failed_run.update(
                status="error",
                completed_at=identity_trace.utc_now(),
                error="test failure",
            )
            with (
                mock.patch.object(
                    identity_trace, "execute_source", return_value=(failed_run, [])
                ),
                mock.patch("sys.stdout"),
            ):
                self.assertEqual(identity_trace.run_command(args), 0)
            case = identity_trace.read_json(root / "case" / "case.json")
            self.assertEqual(case["runs"][0]["status"], "error")
            self.assertEqual(identity_trace.validate_case(root / "case"), [])

    def test_excluded_sources_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            case_dir = self.make_case(Path(name))
            case = identity_trace.read_json(case_dir / "case.json")
            self.assertEqual(case["configuration"]["selected_sources"], [])
            self.assertEqual(
                case["configuration"]["excluded_sources"],
                sorted(identity_trace.SOURCES),
            )
            self.assertIn("Excluded sources:", (case_dir / "report.md").read_text())


if __name__ == "__main__":
    unittest.main()
