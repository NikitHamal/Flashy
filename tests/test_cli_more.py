"""More tests for Flashy CLI helpers, sessions, stats, completions, and banner."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*args, env_extra=None, input_text=""):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "cli.py", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        input=input_text,
        timeout=30,
    )


class FlashyThemeTests(unittest.TestCase):
    def test_theme_list(self):
        result = _run_cli("--no-color", "theme", "list")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("dracula", result.stdout)

    def test_theme_set_unknown(self):
        result = _run_cli("--no-color", "theme", "set", "nope-not-a-theme")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown theme", result.stderr)

    def test_theme_set_persists(self):
        result = _run_cli("--no-color", "theme", "set", "solarized")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        show = _run_cli("--no-color", "theme", "show")
        self.assertIn("solarized", show.stdout)
        # Reset
        _run_cli("--no-color", "theme", "set", "default")


class FlashyStatsTests(unittest.TestCase):
    def test_stats_json(self):
        result = _run_cli("--json", "stats")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("summary", payload)
        self.assertIn("Sessions", payload["summary"])


class FlashyLogsTests(unittest.TestCase):
    def test_logs_path(self):
        result = _run_cli("--no-color", "logs", "--path")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(result.stdout.strip().endswith("flashy.log"))


class FlashySessionTests(unittest.TestCase):
    def test_session_list_empty(self):
        result = _run_cli("--json", "session", "list")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, list)


class FlashyCompletionsTests(unittest.TestCase):
    def test_completions_bash(self):
        result = _run_cli("--no-color", "completions", "bash")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("complete -F", result.stdout)
        self.assertIn("chat", result.stdout)

    def test_completions_zsh(self):
        result = _run_cli("--no-color", "completions", "zsh")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("compdef", result.stdout)

    def test_completions_fish(self):
        result = _run_cli("--no-color", "completions", "fish")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("complete -c flashy", result.stdout)

    def test_completions_powershell(self):
        result = _run_cli("--no-color", "completions", "powershell")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Register-ArgumentCompleter", result.stdout)

    def test_completions_list(self):
        result = _run_cli("--no-color", "completions", "--list")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        for shell in ("bash", "zsh", "fish", "powershell"):
            self.assertIn(shell, result.stdout)


class FlashySessionsLibTests(unittest.TestCase):
    def test_export_markdown(self):
        from flashy_cli.sessions import Session, Message, export, auto_title

        session = Session(
            id="abc123",
            title="Test session",
            workspace=os.getcwd(),
            provider="g4f",
            model="gpt-test",
            reasoning="medium",
            created_at=0.0,
            updated_at=0.0,
            messages=[
                Message(role="user", content="hello"),
                Message(role="assistant", content="hi there"),
            ],
        )
        filename, content = export(session, "md")
        self.assertTrue(filename.endswith(".md"))
        self.assertIn("Test session", content)
        self.assertIn("hello", content)
        self.assertIn("hi there", content)

        filename, content = export(session, "json")
        self.assertTrue(filename.endswith(".json"))
        payload = json.loads(content)
        self.assertEqual(payload["id"], "abc123")
        self.assertEqual(len(payload["messages"]), 2)

    def test_auto_title(self):
        from flashy_cli.sessions import auto_title

        self.assertEqual(auto_title(""), "new session")
        self.assertEqual(auto_title("   \n  "), "new session")
        self.assertTrue(len(auto_title("Refactor the auth flow please")) > 0)


class FlashyFormattingTests(unittest.TestCase):
    def test_extract_attachments(self):
        from flashy_cli.formatting import extract_attachments

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "snippet.py"
            target.write_text("print('hi')", encoding="utf-8")
            cleaned, found = extract_attachments("please review @snippet.py", tmp)
            self.assertEqual(len(found), 1)
            self.assertIn("snippet.py", found[0][0])
            self.assertIn("print", found[0][1])
            self.assertIn("@snippet.py", cleaned)

    def test_extract_attachments_missing(self):
        from flashy_cli.formatting import extract_attachments

        cleaned, found = extract_attachments("@missing.py", os.getcwd())
        self.assertEqual(found, [])

    def test_truncate(self):
        from flashy_cli.formatting import truncate

        self.assertEqual(truncate("hello", 10), "hello")
        self.assertIn("…", truncate("a" * 200, 20))


class FlashyBannerTests(unittest.TestCase):
    def test_build_welcome_no_logo(self):
        from io import StringIO

        from rich.console import Console

        from flashy_cli.banner import build_welcome

        panel = build_welcome(
            workspace=os.getcwd(),
            provider="g4f",
            model="gpt-test",
            reasoning="medium",
            mode="clean",
            session_id="abcdef12345",
            show_logo=False,
        )
        # Render the panel through a Rich console into a string buffer.
        buf = StringIO()
        Console(file=buf, force_terminal=False, color_system=None).print(panel)
        text = buf.getvalue()
        self.assertIn("g4f", text)
        self.assertIn("gpt-test", text)


class FlashyDoctorTests(unittest.TestCase):
    def test_doctor_json(self):
        result = _run_cli("--json", "doctor")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("total", payload)
        self.assertIn("passed", payload)
        self.assertIn("failed", payload)


class FlashyInitTests(unittest.TestCase):
    def test_init_yes(self):
        # Use a temporary FLASHY_DATA_DIR to avoid clobbering user data.
        with tempfile.TemporaryDirectory() as tmp:
            env = {"FLASHY_DATA_DIR": tmp}
            result = _run_cli("--no-color", "init", "-y", env_extra=env)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Flashy config is ready", result.stdout)


if __name__ == "__main__":
    unittest.main()

