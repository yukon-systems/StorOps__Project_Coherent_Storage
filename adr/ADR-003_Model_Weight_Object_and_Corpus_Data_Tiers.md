# ADR-003: Model Weight, Object, and Corpus Data Tiers

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Use immutable, versioned, content-addressed object/file tiers for model weights, tokenizers, adapters, RAG corpus chunks, generated artifacts, and checkpoints, with RDMA-first delivery paths where supported and POSIX/object compatibility where required.

## Context

LLM serving systems need two storage personalities. The hot KV tier is request-shaped and latency critical. Model weights, adapters, tokenizers, RAG corpora, embeddings, and batch artifacts are different: they are large, versioned, often immutable, prefetchable, and must be reproducible. RDMA-first object storage and DPU-offloaded storage research show a practical direction: keep a small control plane for names, capabilities, and manifests, and move data through high-throughput RDMA paths when possible.

The baseline architecture already uses NVMe-oF/OpenZFS and DPU/SPDK-capable target paths. This ADR adds an inference object/corpus tier above that substrate. OCP inference cluster guidance also separates gateway, scale-out, storage, and distributed inference profiles, so model/corpus delivery must be schedulable by fabric profile rather than a best-effort shared bulk path.

## Decision

- Represent every online model as a signed manifest of content-addressed shards.
- Store model weights, tokenizer files, adapters, prompts/templates, embedding-model artifacts, corpus chunks, vector-index build products, and batch outputs in immutable object/file namespaces.
- Provide a POSIX-compatible view only where frameworks require filesystem access. The source of truth remains the manifest and object namespace.
- Prefer RDMA-first object/file delivery for high-throughput weight loads, corpus scans, and embedding/index rebuilds.
- Use the required DPU/SmartNIC storage-path hardware for object client/transport acceleration, tenant isolation, encryption, and telemetry; each service profile still requires platform qualification before production-like promotion.
- Keep local T2 copies of hot model shards and corpus chunks on inference or storage-client nodes using explicit prefetch and eviction policy.
- Tag model, corpus, embedding, index-build, and artifact movement with fabric class, rack/power domain, and background/interactive priority metadata before admission.

## Object namespace policy

| Namespace | Contents | Mutability | Default tier |
| --- | --- | --- | --- |
| `models/` | Base weights, safetensors, engine plans, runtime-specific layouts | Immutable per digest | T2/T3 |
| `tokenizers/` | Tokenizer model, vocabulary, normalization config | Immutable per digest | T2/T3 |
| `adapters/` | LoRA, fine-tune deltas, routing config | Immutable per digest | T2/T3 |
| `corpus/` | RAG source chunks, normalized text, media derivatives | Immutable per corpus snapshot | T3/T4, hot chunks in T2 |
| `embeddings/` | Embedding vectors, quantized codes, metadata | Immutable per embedding model and corpus snapshot | T2/T3 |
| `indexes/` | HNSW/IVF/PQ or equivalent vector index build products | Immutable per build | T1/T2 hot, T3 durable |
| `artifacts/` | Batch inference outputs, evaluation traces, checkpoints | Append or immutable | T3/T4 |

## Model-load policy

- Model admission requires that required shards are either resident in T2 or prefetchable inside the model's load SLO.
- Large model loads must not share the same lossless priority as KV hydration unless explicitly approved.
- Weight prefetching is scheduled before GPU allocation when possible.
- Model shard checksums are verified before serving traffic.
- Runtime-specific transformed formats are cached as derived artifacts with provenance back to the source manifest.

## Corpus and artifact policy

- Corpus chunks are immutable and referenced by corpus snapshot ID.
- Re-indexing creates a new index version instead of mutating the active index in place.
- Generated artifacts and evaluation outputs are written outside the interactive inference hot path.
- Checkpoints and batch outputs may use throughput-optimized paths and do not receive priority over interactive KV hydration.

## Positive consequences

- Model and RAG state becomes reproducible and audit-friendly.
- Weight loads can be optimized independently from hot KV-cache operations.
- RDMA object delivery can improve throughput without forcing all applications to use raw block devices.
- Local hot copies reduce repeated model and corpus reads from shared storage.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| POSIX compatibility hides manifest drift | Require signed manifests and verify digests before exposing POSIX views. |
| Model prefetch saturates the fabric | Use separate traffic class, admission control, and rate limits for model/object loads. |
| Derived runtime artifacts become stale | Include source digest, runtime version, GPU architecture, and transformation profile in derived artifact names. |
| Object store RDMA security is too broad | Mediate capabilities through DPU or trusted storage gateways; avoid exposing unrestricted rkeys to tenants. |
| Bulk model or corpus movement violates fabric or power envelope | Pre-stage by rack/rail and budget large transfers through ADR-004 traffic classes plus ADR-007 admission. |

## Acceptance criteria

- A model can be loaded from a manifest and every shard checksum is verified before traffic is admitted.
- A model alias can be updated without mutating existing immutable model objects.
- RAG corpus chunks and vector indexes are addressable by corpus snapshot and embedding model version.
- A canary model-load benchmark reports p50/p95/p99 load time and fabric impact.
- POSIX compatibility views can be regenerated from manifests.
- Model/corpus prefetch reports traffic class, rack/rail placement, power domain, and scheduler admission decision.

## Source documents

| ID | Use |
| --- | --- |
| A0 | Existing OpenZFS/NVMe-oF and DPU target substrate. |
| R03 | HPC LLM serving, RAG pipeline, embedding service, and LLM metrics. |
| R05 | RDMA-first object storage and SmartNIC offload pattern. |
| R16 | Direct storage access pressure from GPU-centric workloads. |
| R21 | HPC storage hierarchy and burst-buffer context. |
| R34, R36, R37 | OCP inference/data-center/training fabric guidance for cluster profiles, gateway/storage separation, lifecycle observability, and power-aware placement. |

