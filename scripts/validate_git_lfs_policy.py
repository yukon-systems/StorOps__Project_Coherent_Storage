#!/usr/bin/env python3
"""Validate repository Git LFS policy before origin pushes.

This script is intentionally portable: it only depends on Python 3, Git, and
Git LFS. The tracked pre-push hook invokes it before delegating to
`git lfs pre-push`.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
from dataclasses import dataclass

POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"
MASTER_REL = pathlib.Path("policy/git-lfs/gitattributes.master")
HOOKS_PATH = "scripts/git-hooks"


@dataclass
class Failure:
    message: str
    remediation: str


def run(
    cmd: list[str],
    *,
    cwd: pathlib.Path | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


def git(args: list[str], *, cwd: pathlib.Path | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=cwd, check=check)


def repo_root() -> pathlib.Path:
    result = git(["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise SystemExit("not inside a Git repository")
    return pathlib.Path(result.stdout.strip())


def parse_lfs_endpoint(env_output: str) -> str:
    for line in env_output.splitlines():
        if line.startswith("Endpoint="):
            value = line.removeprefix("Endpoint=").strip()
            return value.split(" (auth=", 1)[0].strip()
    return ""


def locksverify_config_key(endpoint: str) -> str:
    return f"lfs.{endpoint}.locksverify"


def is_true(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def check_git_lfs_installed() -> list[Failure]:
    result = run(["git", "lfs", "version"])
    if result.returncode == 0:
        return []
    return [
        Failure(
            "git-lfs is not installed or not on PATH",
            "Install git-lfs, then run scripts/bootstrap_git_lfs_policy.sh.",
        )
    ]


def check_lfs_enabled(root: pathlib.Path) -> list[Failure]:
    failures: list[Failure] = []
    expected = {
        "filter.lfs.process": "git-lfs filter-process",
        "filter.lfs.clean": "git-lfs clean",
        "filter.lfs.smudge": "git-lfs smudge",
        "filter.lfs.required": "true",
    }
    for key, required_fragment in expected.items():
        result = git(["config", "--get", key], cwd=root)
        value = result.stdout.strip() if result.returncode == 0 else ""
        if required_fragment not in value:
            failures.append(
                Failure(
                    f"{key} is not enabled for Git LFS",
                    "Run git lfs install --local, or scripts/bootstrap_git_lfs_policy.sh.",
                )
            )
    repo_format = git(["config", "--get", "lfs.repositoryformatversion"], cwd=root)
    if repo_format.returncode != 0 or repo_format.stdout.strip() != "0":
        failures.append(
            Failure(
                "lfs.repositoryformatversion is not set to 0",
                "Run git lfs install --local, or scripts/bootstrap_git_lfs_policy.sh.",
            )
        )
    return failures


def check_hooks_path(root: pathlib.Path) -> list[Failure]:
    result = git(["config", "--local", "--get", "core.hooksPath"], cwd=root)
    value = result.stdout.strip() if result.returncode == 0 else ""
    if value == HOOKS_PATH:
        return []
    return [
        Failure(
            f"core.hooksPath is '{value or '<unset>'}', expected '{HOOKS_PATH}'",
            "Run scripts/bootstrap_git_lfs_policy.sh to install the repo-local pre-push policy hook.",
        )
    ]


def check_push_safety_configs(root: pathlib.Path) -> list[Failure]:
    result = git(["config", "--bool", "--get", "lfs.allowincompletepush"], cwd=root)
    if result.returncode == 0 and is_true(result.stdout):
        return [
            Failure(
                "lfs.allowincompletepush is true",
                "Set git config --local lfs.allowincompletepush false or remove the override; "
                "pushes must not proceed with missing LFS objects.",
            )
        ]
    return []


def check_locksverify(root: pathlib.Path, remote_name: str) -> list[Failure]:
    if remote_name != "origin":
        return []
    env = run(["git", "lfs", "env"], cwd=root)
    if env.returncode != 0:
        return [Failure("git lfs env failed", "Run git lfs install --local, then retry.")]
    endpoint = parse_lfs_endpoint(env.stdout)
    if not endpoint:
        return [
            Failure(
                "could not determine Git LFS endpoint",
                "Verify origin has an LFS endpoint, then run scripts/bootstrap_git_lfs_policy.sh.",
            )
        ]
    key = locksverify_config_key(endpoint)
    result = git(["config", "--local", "--bool", "--get", key], cwd=root)
    if result.returncode == 0 and is_true(result.stdout):
        return []
    return [Failure(f"local {key} is not true", f"Run: git config --local '{key}' true")]


def parse_gitattributes_patterns(text: str) -> tuple[list[str], list[Failure]]:
    patterns: list[str] = []
    failures: list[Failure] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) != 5 or parts[1:] != ["filter=lfs", "diff=lfs", "merge=lfs", "-text"]:
            failures.append(
                Failure(
                    f"invalid .gitattributes line {lineno}: {line}",
                    "Use policy/git-lfs/gitattributes.master as the source of truth.",
                )
            )
            continue
        patterns.append(parts[0])
    if patterns != sorted(patterns, key=lambda value: value.lower()):
        failures.append(Failure("LFS patterns are not alphanumerically sorted", "Sort policy/git-lfs/gitattributes.master and copy it to .gitattributes."))
    duplicates = sorted({pattern for pattern in patterns if patterns.count(pattern) > 1})
    if duplicates:
        failures.append(Failure(f"duplicate LFS patterns: {', '.join(duplicates)}", "Remove duplicate patterns from policy/git-lfs/gitattributes.master."))
    return patterns, failures


def check_gitattributes(root: pathlib.Path) -> list[Failure]:
    master = root / MASTER_REL
    repo_attrs = root / ".gitattributes"
    failures: list[Failure] = []
    if not master.exists():
        failures.append(Failure(f"missing {MASTER_REL}", "Restore the master Git LFS attributes policy file."))
        return failures
    if not repo_attrs.exists():
        failures.append(Failure("missing .gitattributes", f"Copy {MASTER_REL} to .gitattributes."))
        return failures
    master_text = master.read_text()
    repo_text = repo_attrs.read_text()
    if master_text != repo_text:
        failures.append(Failure(".gitattributes differs from policy/git-lfs/gitattributes.master", f"Run: cp {MASTER_REL} .gitattributes"))
    _, parse_failures = parse_gitattributes_patterns(master_text)
    failures.extend(parse_failures)
    return failures


def attr_filter_for_path(root: pathlib.Path, path: str) -> str:
    result = git(["check-attr", "-z", "filter", "--", path], cwd=root)
    if result.returncode != 0:
        return ""
    parts = result.stdout.split("\0")
    return parts[2] if len(parts) >= 3 else ""


def check_lfs_tracked_blobs_are_pointers(root: pathlib.Path) -> list[Failure]:
    result = git(["ls-files", "-z"], cwd=root)
    if result.returncode != 0:
        return [Failure("git ls-files failed", "Check repository health before pushing.")]
    failures: list[Failure] = []
    for path in [item for item in result.stdout.split("\0") if item]:
        if attr_filter_for_path(root, path) != "lfs":
            continue
        size_result = git(["cat-file", "-s", f":{path}"], cwd=root)
        if size_result.returncode != 0:
            continue
        size = int(size_result.stdout.strip())
        if size > 1024:
            failures.append(
                Failure(
                    f"{path} is LFS-tracked by attributes but index blob is {size} bytes, "
                    "not an LFS pointer",
                    "Run git lfs migrate import --fixup for unpublished commits, "
                    "or migrate history intentionally.",
                )
            )
            continue
        blob = git(["cat-file", "-p", f":{path}"], cwd=root)
        if blob.returncode != 0 or not blob.stdout.encode().startswith(POINTER_PREFIX):
            failures.append(
                Failure(
                    f"{path} is LFS-tracked by attributes but is not stored as an LFS pointer",
                    "Re-add the file after Git LFS is enabled, or run git lfs migrate import --fixup.",
                )
            )
    return failures


def validate(root: pathlib.Path, *, remote_name: str, skip_hooks_path: bool = False) -> list[Failure]:
    failures: list[Failure] = []
    failures.extend(check_git_lfs_installed())
    if failures:
        return failures
    failures.extend(check_lfs_enabled(root))
    if not skip_hooks_path:
        failures.extend(check_hooks_path(root))
    failures.extend(check_locksverify(root, remote_name))
    failures.extend(check_push_safety_configs(root))
    failures.extend(check_gitattributes(root))
    failures.extend(check_lfs_tracked_blobs_are_pointers(root))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository Git LFS policy.")
    parser.add_argument("--remote-name", default="origin", help="Git remote name supplied by pre-push; locksverify is enforced for origin.")
    parser.add_argument("--remote-url", default="", help="Git remote URL supplied by pre-push; accepted for diagnostics.")
    parser.add_argument("--skip-hooks-path", action="store_true", help="Do not require core.hooksPath=scripts/git-hooks.")
    args = parser.parse_args(argv)

    root = repo_root()
    failures = validate(root, remote_name=args.remote_name, skip_hooks_path=args.skip_hooks_path)
    if not failures:
        print("Git LFS policy validation passed.")
        return 0

    print("Git LFS policy validation failed:", file=sys.stderr)
    for index, failure in enumerate(failures, start=1):
        print(f"  {index}. {failure.message}", file=sys.stderr)
        print(f"     Remediation: {failure.remediation}", file=sys.stderr)
    if args.remote_url:
        print(f"Remote: {args.remote_name} {args.remote_url}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
