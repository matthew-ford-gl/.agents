import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit_session.py")
SUMMARIES = """SOLID: 0 critical, 0 major, 0 minor.
Naming & Clean Code: 0 critical, 0 major, 0 minor.
Complexity: 0 critical, 0 major, 0 minor.
Code Smells & Duplication: 0 critical, 0 major, 0 minor.
Chunk total: 0.
"""


class AuditSessionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.standard = self.root / "standard.md"
        self.standard.write_text("standard", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def run_script(self, *arguments, check=True, env=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, arguments)],
            check=check,
            capture_output=True,
            text=True,
            env=env,
        )

    def create_session(self, sizes, name="session"):
        paths = []
        for index, size in enumerate(sizes):
            path = f"src/file-{index}.py"
            source = self.repo / path
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"x" * size)
            paths.append(path)
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps(paths), encoding="utf-8")
        result = self.run_script(
            "init",
            "--repo", self.repo,
            "--target", "src",
            "--revision", "abcdef123456",
            "--standard", self.standard,
            "--manifest", manifest,
            "--context-root", self.root / "context",
            "--session", name,
        )
        return Path(result.stdout.strip()), paths

    def result_file(self, name, paths, incomplete=False):
        result = self.root / name
        lines = ["Files inspected:", *(f"- {path}" for path in paths), "", SUMMARIES]
        lines.append("INCOMPLETE: true" if incomplete else "INCOMPLETE: false")
        result.write_text("\n".join(lines), encoding="utf-8")
        return result

    def test_init_creates_bounded_chunks_and_resumes_matching_session(self):
        session, _ = self.create_session([10_000, 10_000, 15_000, 40_000])
        state = json.loads((session / "state.json").read_text(encoding="utf-8"))
        self.assertEqual([2, 1, 1], [chunk["file_count"] for chunk in state["chunks"]])
        self.assertTrue(state["chunks"][-1]["oversized_single_file"])
        resumed, _ = self.create_session([10_000, 10_000, 15_000, 40_000])
        self.assertEqual(session, resumed)
        self.assertEqual(state["created_at"], json.loads((session / "state.json").read_text())["created_at"])

    def test_accepts_complete_result_and_reaches_synthesis(self):
        session, paths = self.create_session([100])
        result = self.result_file("complete.md", paths)
        self.run_script("record", "--session", session, "--chunk", "C0001", "--result", result)
        state = json.loads((session / "state.json").read_text(encoding="utf-8"))
        self.assertEqual("ready-for-synthesis", state["status"])
        self.assertEqual("accepted", state["chunks"][0]["status"])
        self.assertTrue((session / "results" / "C0001-attempt-1.md").exists())

    def test_rejects_sampling_and_requeues_halved_children(self):
        session, paths = self.create_session([100, 100, 100, 100])
        result = self.result_file("sampled.md", paths[:2])
        self.run_script("record", "--session", session, "--chunk", "C0001", "--result", result)
        state = json.loads((session / "state.json").read_text(encoding="utf-8"))
        self.assertEqual("rejected", state["chunks"][0]["status"])
        children = [chunk for chunk in state["chunks"] if chunk["parent"] == "C0001"]
        self.assertEqual([2, 2], [chunk["file_count"] for chunk in children])
        self.assertTrue(all(chunk["status"] == "pending" for chunk in children))
        wave = json.loads(self.run_script("next-wave", "--session", session).stdout)
        self.assertEqual([child["id"] for child in children], [chunk["id"] for chunk in wave["chunks"]])

    def test_blocks_incomplete_single_file(self):
        session, paths = self.create_session([100])
        result = self.result_file("incomplete.md", paths, incomplete=True)
        self.run_script("record", "--session", session, "--chunk", "C0001", "--result", result)
        state = json.loads((session / "state.json").read_text(encoding="utf-8"))
        self.assertEqual("blocked", state["status"])
        self.assertEqual("failed", state["chunks"][0]["status"])

    def test_context_storage_path_is_the_primary_default(self):
        source = self.repo / "src" / "file.py"
        source.parent.mkdir(parents=True)
        source.write_text("value = 1", encoding="utf-8")
        manifest = self.root / "context-manifest.json"
        manifest.write_text(json.dumps(["src/file.py"]), encoding="utf-8")
        configured = self.root / "configured-context"
        env = os.environ.copy()
        env["CONTEXT_STORAGE_PATH"] = str(configured)
        result = self.run_script(
            "init",
            "--repo", self.repo,
            "--target", "src",
            "--revision", "abcdef123456",
            "--standard", self.standard,
            "--manifest", manifest,
            "--session", "environment-session",
            env=env,
        )
        self.assertEqual(configured.resolve() / "repo" / "quality-audit" / "environment-session", Path(result.stdout.strip()))

    def test_rejects_session_name_reuse_with_different_inputs(self):
        self.create_session([100])
        result = self.run_script(
            "init",
            "--repo", self.repo,
            "--target", "different",
            "--revision", "abcdef123456",
            "--standard", self.standard,
            "--manifest", self.root / "manifest.json",
            "--context-root", self.root / "context",
            "--session", "session",
            check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("different inputs", result.stderr)


if __name__ == "__main__":
    unittest.main()
