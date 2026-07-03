import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from flashy_cli.runtime import redact_config
from backend.tools import Tools


ROOT = Path(__file__).resolve().parents[1]


class FlashyCliSmokeTests(unittest.TestCase):
    def test_version_json(self):
        result = subprocess.run(
            [sys.executable, "cli.py", "--json", "version"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["flashy_cli"], "0.3.0")
        self.assertIn("python", payload)

    def test_redacts_secret_like_config_values(self):
        redacted = redact_config({"api_key": "secret", "model": "demo", "nested": {"token": "abc"}})
        self.assertEqual(redacted["api_key"], "***")
        self.assertEqual(redacted["model"], "demo")
        self.assertEqual(redacted["nested"]["token"], "***")

    def test_tools_are_workspace_bound_and_usable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "hello.txt").write_text("hello flashy", encoding="utf-8")
            tools = Tools(str(root))
            self.assertIn("hello flashy", tools.read_file("hello.txt"))
            self.assertIn("hello.txt", tools.list_dir("."))
            self.assertIn("outside the workspace", tools.list_dir(str(root.parent)))


if __name__ == "__main__":
    unittest.main()
