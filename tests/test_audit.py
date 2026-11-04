import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_context_budget.cli import MAX_BYTES, analyze, discover, main


class AuditTests(unittest.TestCase):
    def test_explicit_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            target = p / "AGENTS.md"
            target.write_text("content")
            link = p / "CLAUDE.md"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "Symbolic"):
                analyze(link)

    def test_directory_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            link = p / "linked"
            link.symlink_to(p, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "Symbolic"):
                analyze(link)

    def test_nested_and_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "sub").mkdir()
            (p / "sub" / "AGENTS.md").write_text("abc")
            (p / ".git").mkdir()
            (p / ".git" / "CLAUDE.md").write_text("skip")
            self.assertEqual([e["path"] for e in analyze(p)["files"]], ["sub/AGENTS.md"])

    def test_limit_exact(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            p.write_bytes(b"x" * MAX_BYTES)
            self.assertEqual(analyze(p)["totals"]["bytes"], MAX_BYTES)

    def test_limit_over(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            p.write_bytes(b"x" * (MAX_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "limit"):
                analyze(p)

    def test_duplicate_normalization(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "AGENTS.md").write_text("Always review the changes before publishing anything.\n")
            (p / "GEMINI.md").write_text("  ALWAYS   review the changes before publishing anything.  ")
            self.assertEqual(len(analyze(p)["duplicate_paragraphs"]), 1)

    def test_no_content_in_json(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "AGENTS.md").write_text("PRIVATE_TOKEN_EXAMPLE")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([d, "--json"]), 0)
            self.assertNotIn("PRIVATE_TOKEN_EXAMPLE", output.getvalue())
            json.loads(output.getvalue())

    def test_oswalk_error_not_silent(self):
        with tempfile.TemporaryDirectory() as d:
            def fail_walk(root, followlinks, onerror):
                onerror(PermissionError("private path"))
                yield from ()
            with patch("agent_context_budget.cli.os.walk", fail_walk):
                with self.assertRaisesRegex(ValueError, "traverse"):
                    discover(Path(d))

    def test_input_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            raw = b"\xef\xbb\xbfExample\r\n"
            p.write_bytes(raw)
            analyze(p)
            self.assertEqual(p.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
