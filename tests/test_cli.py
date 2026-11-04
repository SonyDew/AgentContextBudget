import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from agent_context_budget.cli import analyze, main


class AnalyzerTests(unittest.TestCase):
    def test_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(analyze(Path(d))["totals"]["files"], 0)

    def test_duplicate_and_sizes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            paragraph = "This instruction must be repeated in both files for the duplicate report."
            (p / "AGENTS.md").write_text(paragraph + "\n")
            (p / "CLAUDE.md").write_text(paragraph + "\n")
            report = analyze(p)
            self.assertEqual(report["totals"]["files"], 2)
            self.assertEqual(len(report["duplicate_paragraphs"]), 1)

    def test_no_duplicate_within_one_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            p.write_text(("An instruction paragraph long enough to count as a duplicate.\n\n") * 2)
            self.assertEqual(analyze(p)["duplicate_paragraphs"], [])

    def test_symlinks_and_ignored_directories(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "AGENTS.md").write_text("ok")
            (p / "node_modules").mkdir()
            (p / "node_modules" / "CLAUDE.md").write_text("ignored")
            (p / "GEMINI.md").symlink_to(p / "AGENTS.md")
            self.assertEqual(analyze(p)["totals"]["files"], 1)

    def test_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            p.write_bytes(b"\xff")
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                analyze(p)

    def test_large_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            p.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "limit"):
                analyze(p)

    def test_cli_json_does_not_print_contents(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "AGENTS.md").write_text("SECRET_DO_NOT_PRINT")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([d, "--json"]), 0)
            self.assertNotIn("SECRET_DO_NOT_PRINT", output.getvalue())
            self.assertEqual(json.loads(output.getvalue())["totals"]["files"], 1)

    def test_bad_path_does_not_echo(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            self.assertEqual(main(["/nonexistent/secret-value"]), 2)
        self.assertNotIn("secret-value", error.getvalue())

    def test_source_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            p.write_bytes(b"hello\r\n")
            analyze(Path(d))
            self.assertEqual(p.read_bytes(), b"hello\r\n")


if __name__ == "__main__":
    unittest.main()
