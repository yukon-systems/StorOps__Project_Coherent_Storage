# Git LFS Policy and Push-Time Validation

## Purpose

All Project Coherent Storage repositories that use Git LFS must use a repo-local
LFS policy rather than relying only on developer-global Git configuration. The
policy enforces these invariants before any `origin` push:

1. `git-lfs` is installed and usable.
2. Git LFS filters are enabled for the repository.
3. `core.hooksPath` points at the tracked hook directory `scripts/git-hooks`.
4. The effective `origin` LFS endpoint has a local `lfs.<url>.locksverify=true`
   configuration entry.
5. `.gitattributes` is byte-for-byte identical to
   `policy/git-lfs/gitattributes.master`.
6. Tracked files that match LFS attributes are Git LFS pointer blobs in the Git
   index, not accidental inline binary blobs.

## Bootstrap

Run this once per clone:

```bash
scripts/bootstrap_git_lfs_policy.sh
```

The bootstrap script performs the repo-local setup:

```bash
git lfs install --local --skip-repo
git config --local core.hooksPath scripts/git-hooks
endpoint="$(git lfs env | sed -n 's/^Endpoint=//p' | sed 's/ (auth=.*//' | head -n 1)"
git config --local "lfs.${endpoint}.locksverify" true
python3 scripts/validate_git_lfs_policy.py --remote-name origin
```

The tracked hook `scripts/git-hooks/pre-push` runs
`scripts/validate_git_lfs_policy.py` before delegating to `git lfs pre-push`.
This preserves normal Git LFS upload behavior while adding a policy gate before
`origin` pushes.

## Master `.gitattributes`

`policy/git-lfs/gitattributes.master` is the source of truth. The repository
root `.gitattributes` must be an exact copy:

```bash
cp policy/git-lfs/gitattributes.master .gitattributes
python3 scripts/validate_git_lfs_policy.py --remote-name origin
```

The master file is intentionally extension-oriented and sorted. It includes
common archives, packages, disk images, office/media assets, machine-learning
artifacts (`*.gguf`, `*.onnx`, `*.safetensors`, `*.pt`, `*.parquet`, etc.),
CXL/storage research artifacts, and generated diagram/image formats.

## Git LFS API Quality Gates

Primary Git LFS interfaces that matter for repo quality assurance:

- Batch transfer API: clients request upload/download actions with
  `POST <lfs-url>/objects/batch`. Validation should treat upload/download
  failures as repository health or service health signals, not just transport
  noise.
- File locking API: clients create/list/delete locks and verify push safety via
  `POST <lfs-url>/locks/verify`. Because all approved Git hosts support locking,
  `lfs.<url>.locksverify=true` is mandatory for `origin`.
- Transfer verification: Batch API upload responses may include a `verify`
  action. Test-server workflows should cover this path when validating custom
  LFS endpoints or proxy behavior.

## Coherence-CE LFS Backend Target

ADR-026 defines the long-term Coherence-CE object chunking and manifest model
for a future Git LFS backend. Until that gateway passes compatibility and
failure-mode gates, Git LFS clients must continue to use a conventional Git LFS
API endpoint. Coherence-CE may shadow-copy LFS objects for validation, but it
must not replace the client-facing LFS API with raw S3 or Coherence-native REST.

Promotion to a Coherence-backed LFS endpoint requires:

- successful Git LFS Batch API upload/download tests;
- lock create/list/delete/verify tests;
- SHA256 OID and size validation;
- `git lfs fsck` against promoted repositories;
- safe garbage collection of abandoned partial uploads;
- documented fallback or mirror behavior during Coherence-CE maintenance.



## Lockable Attribute Posture

The policy enforces `locksverify=true` for `origin` pushes, but it does not
blanket-add the `.gitattributes` `lockable` attribute to every binary pattern.
The Git LFS wiki documents that `lockable` makes matching files read-only in the
working tree until they are locked. That behavior is useful for selected assets
with human binary edit conflicts, but it is too disruptive as a default for
generated diagrams, model artifacts, archives, and automated build outputs. Add
`lockable` only for file families with explicit workflow ownership rules.

## Git LFS Quality-of-Service Controls

Use these controls deliberately when tuning repository behavior:

- `lfs.allowincompletepush` must not be `true`; incomplete pushes can leave Git
  refs pointing at LFS objects that the remote does not have.
- `lfs.concurrenttransfers` can be tuned per host for large artifact pushes, but
  high values should be validated against host throttling and CI/network limits.
- `lfs.transfer.maxretries` and `lfs.transfer.maxretrydelay` are useful for
  unstable links; prefer explicit host-scoped settings over broad global changes.
- `lfs.activitytimeout`, `lfs.tlstimeout`, and `lfs.keepalive` can be tuned for
  long-haul or high-latency links. Keep defaults unless validation shows timeouts
  are caused by transport latency rather than service failure.
- `lfs.basictransfersonly` should remain unset unless debugging a custom or
  advanced transfer adapter.
- `lfs.skipdownloaderrors` should not be used as a normal development setting; it
  can mask missing artifact availability during checkout.

## Test Server Use

Use `https://github.com/yukon-systems/GitOps__lfs-test-server` as the local
integration target before broad policy changes. That test server implements the
Git LFS API and includes lock endpoints such as `/locks`, `/locks/verify`, and
`/locks/{id}/unlock`.

Suggested local validation workflow:

```bash
git clone https://github.com/yukon-systems/GitOps__lfs-test-server.git /tmp/GitOps__lfs-test-server
cd /tmp/GitOps__lfs-test-server
go test ./...
go build -o /tmp/lfs-test-server .
```

Then run a disposable client repo against that server with `.lfsconfig` pointing
at the test endpoint. Keep this as an integration lane for future changes to
`lfs.<url>.locksverify`, Batch API assumptions, and lock verification behavior.

## Existing Repository Migration

Use migration analysis before rewriting history:

```bash
git lfs migrate info --everything --fixup
```

If the output shows file types that should already be pointers according to
`.gitattributes`, plan the history rewrite explicitly. For unpublished branches
or coordinated maintenance windows:

```bash
git status --short
git lfs migrate import --everything --fixup
git lfs migrate info --everything --fixup
git lfs fsck
git push --force-with-lease --all origin
git push --force-with-lease --tags origin
```

Do not run `git lfs migrate import --everything --fixup` casually on shared
history. It rewrites commit IDs and requires coordinated force-push and clone
repair for collaborators.

## References

- Git LFS API overview: https://github.com/git-lfs/git-lfs/blob/main/docs/api/README.md
- Git LFS Batch API: https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md
- Git LFS File Locking API: https://github.com/git-lfs/git-lfs/blob/main/docs/api/locking.md
- Git LFS File Locking wiki: https://github.com/git-lfs/git-lfs/wiki/File-Locking
- Git LFS configuration: https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-config.adoc
- Git LFS install behavior: https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-install.adoc
- Git LFS migrate: https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-migrate.adoc
- Local LFS test server: https://github.com/yukon-systems/GitOps__lfs-test-server
