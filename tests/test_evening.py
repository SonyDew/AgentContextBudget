import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from agent_context_budget.cli import MAX_BYTES, analyze, main, read_instruction


class EveningTests(unittest.TestCase):
    def test_exact_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            p.write_bytes(b"x" * MAX_BYTES)
            self.assertEqual(analyze(p)["totals"]["bytes"], MAX_BYTES)

    def test_one_byte_over_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            p.write_bytes(b"x" * (MAX_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "limit"):
                analyze(p)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "O_NOFOLLOW unavailable")
    def test_file_replaced_with_symlink_after_discovery(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / "AGENTS.md"
            secret = root / "private.txt"
            secret.write_text("secret contents")
            p.symlink_to(secret)
            with self.assertRaisesRegex(ValueError, "Cannot read"):
                read_instruction(p)

    @unittest.skipUnless(hasattr(os, "mkfifo") and hasattr(os, "O_NONBLOCK"), "FIFO support unavailable")
    def test_fifo_is_not_read(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "AGENTS.md"
            os.mkfifo(p)
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                read_instruction(p)

    def test_no_content_in_json(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "AGENTS.md").write_text("PRIVATE_DATA_123")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main([d, "--json"]), 0)
            self.assertNotIn("PRIVATE_DATA_123", out.getvalue())
            self.assertEqual(json.loads(out.getvalue())["totals"]["files"], 1)

    def test_source_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "CLAUDE.md"
            p.write_bytes(b"hello\r\n")
            analyze(Path(d))
            self.assertEqual(p.read_bytes(), b"hello\r\n")


if __name__ == "__main__":
    unittest.main()
