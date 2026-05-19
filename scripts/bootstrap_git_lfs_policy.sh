#!/bin/sh
set -eu

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

command -v git-lfs >/dev/null 2>&1 || {
    printf >&2 'git-lfs is required; install it before bootstrapping this repository.\n'
    exit 2
}

# Install LFS filter settings locally so this repo remains self-describing even
# on hosts that do not have a user-global ~/.gitconfig LFS setup.
git lfs install --local --skip-repo

# Route Git hooks to the tracked hook directory. The tracked pre-push hook then
# validates policy and delegates to `git lfs pre-push`.
git config --local core.hooksPath scripts/git-hooks

endpoint="$(git lfs env | sed -n 's/^Endpoint=//p' | sed 's/ (auth=.*//' | head -n 1)"
if [ -z "${endpoint}" ]; then
    printf >&2 'Unable to determine Git LFS endpoint from git lfs env.\n'
    exit 1
fi

git config --local "lfs.${endpoint}.locksverify" true
python3 scripts/validate_git_lfs_policy.py --remote-name origin
