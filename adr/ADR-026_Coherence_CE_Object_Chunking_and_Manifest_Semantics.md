# ADR-026: Coherence-CE Object Chunking and Manifest Semantics

**Project:** Project Coherent Storage
**Architecture cycle:** 2026-Q2
**Status:** Proposed
**Generated:** 2026-05-20

## Architecture diagram

![ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics](diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics.png)

Printable sections:

- [Section 01 - protocol mapping](diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics_print-section-01_protocol-mapping.png)
- [Section 02 - manifest commit](diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics_print-section-02_manifest-commit.png)
- [Section 03 - validation and failure semantics](diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics_print-section-03_validation-failure.png)

## Decision summary

Adopt a Coherence-CE internal object chunking and manifest model for large byte objects while preserving external protocol compatibility for S3, Git LFS, REST, and Coherence-native clients.

The IRTF CCNx chunking draft and FLIC draft are useful design references for ordered chunks, final-chunk metadata, chunk-size metadata, content-hash pointers, and manifest traversal. They are not adopted as public wire protocols for Project Coherent Storage. S3 clients continue to see S3 semantics, Git LFS clients continue to see the Git LFS API, and Coherence-native clients see REST resources.

## Context

Project Coherent Storage needs one object substrate that can support:

- S3 object CRUD and multipart upload;
- Git LFS object storage, batch upload/download negotiation, and lock verification;
- RAG source-document storage and immutable extraction provenance;
- model, adapter, tokenizer, benchmark artifact, and result-bundle storage;
- Coherence-CE placement across DRAM/CXL warm tiers, DPU-mediated OpenZFS, RDMA object paths, and mirrored storage nodes.

A single large object cannot be treated as an indivisible unit for every workload. Large objects need resumable transfer, deduplication, checksum validation, partial retry, placement decisions, garbage collection, mirror lag handling, and durability-class policy. At the same time, external clients should not be forced to understand OpenZFS, DPU, RDMA, CXL, or the internal chunk layout.

## Decision

Define every large byte object as an immutable manifest root plus ordered content-addressed chunks.

```json
{
  "manifest_id": "sha256:manifest-root",
  "object_id": "sha256:object-content",
  "namespace": "git-lfs/yukon-systems/repo-name",
  "external_protocol": "git-lfs",
  "chunk_size": 8388608,
  "chunk_count": 128,
  "end_chunk_number": 127,
  "total_size": 1073741824,
  "content_sha256": "...",
  "durability_class": "OBJ-D3",
  "placement_policy": "zfs-mirrored-rdma",
  "commit_state": "committed",
  "chunks": [
    {
      "chunk_number": 0,
      "size": 8388608,
      "sha256": "...",
      "storage_ref": "coherence://object-chunks/...",
      "replication_state": "committed"
    }
  ]
}
```

### Required invariants

- Chunk numbers start at `0` and are contiguous through `end_chunk_number`.
- `chunk_size` is fixed for all non-final chunks in one manifest.
- The final chunk may be smaller than `chunk_size`.
- `content_sha256` identifies the reconstructed full object.
- `manifest_id` identifies the committed manifest representation.
- Readers only observe committed manifests.
- Partial uploads are invisible to readers except through explicit upload-session APIs.
- Garbage collection never deletes a chunk referenced by a committed manifest.
- Semantic RAG chunks are separate from byte-storage chunks.

## Protocol mappings

| External protocol | External identity | Internal mapping | Compatibility rule |
| --- | --- | --- | --- |
| S3 object CRUD | `bucket` + `key` + optional version ID | manifest namespace `s3/{bucket}`, object key metadata, chunks | Preserve S3 method, header, ETag, multipart, and version semantics at the translator boundary. |
| S3 multipart | upload ID + part numbers | upload session + `chunk_number = part_number - 1` when part size policy allows | Preserve S3 part-number behavior externally; normalize internally only after validation. |
| Git LFS | repository + SHA256 OID + size | immutable object manifest with `object_id = sha256:{oid}` | Preserve Git LFS Batch API, basic transfers, lock APIs, and LFS pointer semantics. |
| Coherence-native REST | namespace + object ID | direct manifest and chunk APIs | Expose manifest status, chunk upload, commit, verify, and read APIs. |
| RAG corpus storage | source ID + extraction version | immutable byte manifest plus separate semantic extraction index | Do not conflate storage chunks with retrieval chunks or vector spans. |

## Git LFS gateway rule

A Coherence-backed Git LFS service must be a Git LFS API facade in front of Coherence-CE. It must not ask Git LFS clients to speak S3 or Coherence-native REST.

```text
git-lfs client
  -> Git LFS API facade
    -> Coherence-CE object/chunk REST API
      -> Coherence-CE placement and durability policy
        -> DPU/OpenZFS/RDMA/CXL-backed substrate
```

The facade must implement, at minimum:

- LFS server discovery through repository configuration;
- Batch API `/objects/batch` for `upload` and `download`;
- basic upload/download transfers or an explicitly negotiated custom transfer adapter;
- SHA256 OID and object-size validation;
- lock creation/list/delete/verify if lockable paths are enabled;
- repository/ref authorization hooks from Gitolite or a repo-control-plane service;
- mirror and fallback behavior during Coherence-CE maintenance.

## Manifest lifecycle

| Stage | Behavior | Reader visibility |
| --- | --- | --- |
| Allocate upload session | Client or facade declares object ID, expected size, chunk size, protocol, namespace, and durability class. | Not visible. |
| Upload chunks | Chunks are written idempotently by chunk number and hash. | Not visible. |
| Verify chunks | Coherence-CE validates contiguous chunk numbers, sizes, per-chunk hashes, and full-object hash. | Not visible. |
| Commit manifest | Manifest is atomically committed with an epoch and durability state. | Visible after commit. |
| Serve reads | Readers fetch by external protocol identity and receive protocol-native data or transfer actions. | Visible. |
| Garbage collect | Expired sessions and unreferenced chunks are collected after grace period and mirror checks. | No committed object changes. |

## Failure semantics

| Failure | Required behavior |
| --- | --- |
| Missing chunk | Commit fails with `409 incomplete_manifest`; uploaded chunks remain session-scoped. |
| Wrong chunk hash | Reject chunk or commit with `422 chunk_hash_mismatch`; do not repair silently. |
| Wrong full-object hash | Reject commit with `422 object_hash_mismatch`; preserve evidence for debugging. |
| Duplicate chunk upload | Idempotent success if hash and size match; reject if metadata conflicts. |
| Concurrent manifest commit | Use compare-and-swap on upload session epoch; one committer wins. |
| Reader during upload | Reader sees prior committed version or not found; never sees partial state. |
| Mirror lag | Mark manifest `committed_local` but not `mirror_safe`; external promotion waits. |
| DPU/OpenZFS path degraded | Coherence-CE can accept lower durability only when namespace policy allows; otherwise fail fast. |
| Partial delete | Delete tombstone is manifest-level; chunk GC is asynchronous and safe. |
| RAG extraction failure | Byte object remains valid; semantic extraction state is failed or stale separately. |

## Durability and placement classes

Object manifests must carry durability class independently from protocol identity.

| Class | Use | Minimum behavior |
| --- | --- | --- |
| `OBJ-D0` | Recomputable scratch artifacts | Session-scoped; no durable guarantee. |
| `OBJ-D1` | Local cacheable object | Local committed manifest and checksum validation. |
| `OBJ-D2` | Repo-local important object | Mirrored local durable storage before success. |
| `OBJ-D3` | Git LFS, RAG source, benchmark evidence | Cross-node durable mirror, snapshot eligibility, GC protection. |
| `OBJ-D4` | Release artifacts and public-claim evidence | Cross-node durable mirror plus off-host/archive mirror before promotion. |

Git LFS production objects and RAG source documents default to `OBJ-D3` or stronger.

## S3, LFS, and RAG chunk boundaries

Storage chunking and semantic chunking are separate:

- S3 multipart parts are transfer and object-assembly units.
- Git LFS objects are immutable byte objects identified by SHA256 OID.
- Coherence-CE storage chunks are placement, verification, retry, and GC units.
- RAG semantic chunks are extraction, embedding, vector, and retrieval units.

A PDF in the RAG corpus may have one byte-object manifest, many storage chunks, one extraction manifest, and many semantic retrieval chunks.

## Migration plan for local LFS service

1. Deploy Gitolite for Git refs and branch ACLs.
2. Deploy a conventional Git LFS endpoint as the bootstrap backend.
3. Shadow-copy each LFS object into Coherence-CE and verify SHA256/size.
4. Implement the Coherence-backed Git LFS facade against this ADR and the OpenAPI contract.
5. Promote one low-risk repo to Coherence-backed LFS with conventional LFS as fallback.
6. Require LFS fsck, lock verification, mirror checks, and failure drills before broad promotion.

## Consequences

### Positive

- One internal object model can serve S3, Git LFS, REST, RAG, model, and benchmark artifact workloads.
- Upload retry, hash verification, manifest commit, garbage collection, and mirror safety become consistent.
- Coherence-CE can place object chunks without exposing storage topology to clients.
- RAG byte provenance remains immutable while semantic extraction can evolve independently.

### Negative

- Coherence-CE must implement more object-control semantics than a simple S3 proxy.
- Git LFS compatibility requires exact API behavior; approximate S3 mapping is not enough.
- Garbage collection and mirror safety become correctness-critical.

### Deferred

- A production Git LFS facade implementation.
- A formal JSON Schema for object manifests and upload sessions.
- Custom Git LFS transfer adapters optimized for local Coherence-CE mesh paths.
- Encrypted manifest and chunk policies inspired by FLIC encryption modes.

## Acceptance criteria

- Coherence-CE object manifests include object hash, chunk size, chunk count, end chunk number, per-chunk hashes, durability class, placement policy, and commit state.
- Git LFS clients can use standard Batch API and locking semantics through a facade; clients do not speak S3 directly.
- S3 multipart mappings preserve S3 external semantics and normalize only behind the translator.
- RAG byte-object chunks and semantic retrieval chunks are represented as separate manifests/indexes.
- Readers cannot observe partial uploads.
- Garbage collection is safe for committed manifests and mirror-lag states.

## References

- CCNx Content Object Chunking draft: https://datatracker.ietf.org/doc/draft-irtf-icnrg-ccnxchunking/
- CCNx chunking text: https://www.ietf.org/archive/id/draft-irtf-icnrg-ccnxchunking-04.txt
- File-Like ICN Collections draft: https://datatracker.ietf.org/doc/draft-irtf-icnrg-flic/
- FLIC text: https://www.ietf.org/archive/id/draft-irtf-icnrg-flic-07.txt
- RFC 8569, CCNx Semantics: https://www.rfc-editor.org/rfc/rfc8569
- RFC 8609, CCNx Messages in TLV Format: https://www.rfc-editor.org/rfc/rfc8609
- Git LFS API: https://github.com/git-lfs/git-lfs/blob/main/docs/api/README.md
- Git LFS Batch API: https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md
- Git LFS File Locking API: https://github.com/git-lfs/git-lfs/blob/main/docs/api/locking.md
