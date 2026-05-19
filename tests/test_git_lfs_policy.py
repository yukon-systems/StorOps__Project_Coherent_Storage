import importlib.util
import pathlib
import sys
import stat
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER = ROOT / "policy" / "git-lfs" / "gitattributes.master"
REPO_GITATTRIBUTES = ROOT / ".gitattributes"
HOOK = ROOT / "scripts" / "git-hooks" / "pre-push"
VALIDATOR = ROOT / "scripts" / "validate_git_lfs_policy.py"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_git_lfs_policy.sh"
POLICY_DOC = ROOT / "docs" / "git-lfs-policy.md"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_git_lfs_policy", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GitLfsPolicyFilesTest(unittest.TestCase):
    def test_master_gitattributes_exists_sorted_unique_and_matches_repo_copy(self):
        self.assertTrue(MASTER.exists(), "master LFS gitattributes policy is missing")
        self.assertEqual(
            MASTER.read_text(),
            REPO_GITATTRIBUTES.read_text(),
            ".gitattributes must be generated from policy/git-lfs/gitattributes.master",
        )
        patterns = []
        for line in MASTER.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            self.assertEqual(parts[1:], ["filter=lfs", "diff=lfs", "merge=lfs", "-text"])
            patterns.append(parts[0])
        self.assertEqual(patterns, sorted(patterns, key=lambda value: value.lower()))
        self.assertEqual(len(patterns), len(set(patterns)), "duplicate LFS patterns found")
        for required in ("*.avif", "*.gguf", "*.heic", "*.jxl", "*.onnx", "*.parquet", "*.qcow2", "*.safetensors", "*.zst"):
            self.assertIn(required, patterns)

    def test_bootstrap_preserves_full_endpoint_when_setting_locksverify(self):
        text = BOOTSTRAP.read_text()
        self.assertIn("sed -n 's/^Endpoint=//p'", text)
        self.assertIn("git config --local \"lfs.${endpoint}.locksverify\" true", text)
        self.assertNotIn("awk -F= '/^Endpoint=/{print $2; exit}'", text)

    def test_pre_push_hook_runs_policy_before_git_lfs_pre_push(self):
        text = HOOK.read_text()
        self.assertIn("validate_git_lfs_policy.py", text)
        self.assertIn("git lfs pre-push", text)
        self.assertLess(text.index("validate_git_lfs_policy.py"), text.index("git lfs pre-push"))
        mode = HOOK.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR, "pre-push hook must be executable")

    def test_validator_parses_lfs_endpoint_and_locksverify_key(self):
        module = load_validator()
        env = """git-lfs/3.7.1\nEndpoint=https://example.test/org/repo.git/info/lfs (auth=none)\n  SSH=git@example.test:org/repo.git\n"""
        endpoint = module.parse_lfs_endpoint(env)
        self.assertEqual(endpoint, "https://example.test/org/repo.git/info/lfs")
        self.assertEqual(
            module.locksverify_config_key(endpoint),
            "lfs.https://example.test/org/repo.git/info/lfs.locksverify",
        )

    def test_policy_doc_covers_api_batch_locking_test_server_and_migration(self):
        text = POLICY_DOC.read_text()
        for needle in (
            "objects/batch",
            "locks/verify",
            "GitOps__lfs-test-server",
            "git lfs migrate info --everything --fixup",
            "git lfs migrate import --everything --fixup",
            "lfs.allowincompletepush",
            "Lockable Attribute Posture",
        ):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
