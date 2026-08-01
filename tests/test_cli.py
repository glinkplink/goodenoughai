from __future__ import annotations

import contextlib
import io
import unittest

from goodenough_bench.cli import PLACEHOLDER_EXIT, build_parser, main


class CliTests(unittest.TestCase):
    def test_root_help_describes_scaffold_only(self) -> None:
        help_text = build_parser().format_help()
        self.assertIn("command scaffolding only", help_text)
        self.assertIn("cases", help_text)
        self.assertIn("batch", help_text)

    def test_placeholder_command_does_not_claim_implementation(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["batch", "run"])

        self.assertEqual(result, PLACEHOLDER_EXIT)
        self.assertIn("placeholder only", stderr.getvalue())
        self.assertIn("not implemented", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
