# Project Coherent Storage: Coherence-CE Object Chunking and Git LFS Gateway Design

**Generated:** 2026-05-20
**Status:** Proposed
**Related ADR:** [`ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics.md`](../adr/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics.md)

## Executive summary

Coherence-CE should become the unified object storage mesh for Git LFS, S3, RAG corpus sources, benchmark artifacts, model artifacts, and internal Coherence-native objects. The correct path is not to make clients speak CCNx, nor to make Git LFS clients speak S3. The correct path is to preserve each external protocol and map them into a common internal manifest/chunk model.

The short-term deployment remains conventional and stable: Gitolite handles Git refs and branch authorization, and a conventional Git LFS endpoint provides immediate LFS service. The long-term target is a Coherence-backed Git LFS gateway that implements the Git LFS API while storing object chunks and manifests through Coherence-CE.

## Design goals

- Keep Git clients and Git LFS clients unmodified.
- Keep S3 clients S3-compatible.
- Keep REST clients Coherence-native and explicit.
- Use one internal object/chunk manifest model for durability, placement, retry, and garbage collection.
- Preserve content-addressed integrity using SHA256 object IDs and per-chunk hashes.
- Support local-only, on-premise operation with no inbound external dependency.
- Allow external GitHub mirroring as a deliberate publication action, not as the default collaboration transport.

## Non-goals

- Expose CCNx chunking as a public wire protocol.
- Replace Git LFS Batch or Locking APIs with S3 CRUD.
- Treat RAG semantic chunks as storage chunks.
- Make Coherence-CE the first production LFS backend before passing failure and compatibility gates.

## Control-plane placement

```text
Gitolite
  owns Git refs, branch ACLs, protected namespaces, server-side hooks

Git LFS facade
  owns Git LFS API compatibility, batch negotiation, transfer URLs, locks

Coherence-CE object gateway
  owns chunk upload, manifest commit, verify, read, GC, durability policy

Coherence-CE storage mesh
  owns placement across OpenZFS, DPU/NVMe-oF, RDMA, local cache, archive mirror
```

## Protocol flow

### Git LFS upload

1. Git client pushes normal Git refs to Gitolite.
2. Git LFS client discovers the LFS URL from Git configuration.
3. Git LFS client calls `/objects/batch` with `operation = upload`.
4. LFS facade checks repository/ref authorization through Gitolite policy or a repo-control-plane hook.
5. LFS facade allocates a Coherence-CE upload session with expected OID and size.
6. Client uploads bytes through a basic transfer URL or future custom transfer adapter.
7. Gateway chunks the object, verifies per-chunk and full-object SHA256, and commits the manifest.
8. LFS facade returns success only when the required durability class is satisfied.

### Git LFS download

1. Git LFS client calls `/objects/batch` with `operation = download`.
2. LFS facade resolves repository, OID, size, and authorization.
3. Coherence-CE returns the committed manifest and placement decision.
4. LFS facade streams reconstructed bytes or returns a signed internal transfer URL.
5. Client verifies the LFS object OID as usual.

### S3 multipart upload

1. S3 client starts multipart upload through the S3/REST translator.
2. Translator maps upload ID to a Coherence-CE upload session.
3. S3 part numbers are retained externally.
4. Coherence-CE maps valid parts to internal chunk numbers where policy permits.
5. Completion validates part ordering, sizes, and object hash policy before manifest commit.

## Deployment phases

| Phase | Name | Description | Promotion gate |
| --- | --- | --- | --- |
| 0 | Bootstrap | Gitolite plus conventional Git LFS backend on local storage. | Git push, LFS upload/download, lock verify, backup, and mirrorbot work. |
| 1 | Shadow archive | Conventional LFS remains primary; every LFS object is copied into Coherence-CE. | SHA256 and size match for all shadowed objects; no missing objects after `git lfs fsck`. |
| 2 | Gateway lab | Coherence-backed LFS facade runs against test repos. | Batch API, basic transfer, locks, failures, and GC tests pass. |
| 3 | Low-risk primary | One low-risk repo uses Coherence-CE as primary LFS backend with conventional fallback. | No client changes; fallback tested; mirror lag reported. |
| 4 | Broad promotion | Coherence-CE becomes default LFS object layer for selected repos. | E2ET failure drills, lock verification, mirrorbot, and recovery gates pass. |

## Failure drills

- upload interrupted before manifest commit;
- duplicate chunk upload with matching hash;
- duplicate chunk upload with conflicting hash;
- missing chunk at commit;
- wrong full-object SHA256 at commit;
- lock owner conflict;
- Gitolite ref authorization denied;
- Coherence-CE node loss during upload;
- OpenZFS mirror degradation during commit;
- mirrorbot lag or external sync outage;
- garbage collection under active manifest references.

## Result semantics

| Result | Meaning |
| --- | --- |
| `PASS` | API behavior, hash verification, durability, and lock semantics met the gate. |
| `WARN` | Operation succeeded but mirror lag, fallback, or non-critical telemetry requires review. |
| `FAIL` | Required Git LFS/S3/REST semantics or durability gates failed. |
| `INCONCLUSIVE` | Test environment did not exercise the required backend or failure path. |

## Operational recommendation

Deploy conventional Git LFS first, then shadow every object into Coherence-CE. Coherence-CE should become primary only after the gateway passes compatibility, checksum, lock verification, garbage collection, and failure-mode gates. This preserves immediate developer productivity while moving toward the unified storage mesh.
