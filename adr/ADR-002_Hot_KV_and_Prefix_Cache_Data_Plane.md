# ADR-002: Hot KV and Prefix Cache Data Plane

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Architecture diagram

![ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane](diagrams/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.png)

## Decision summary

Make Coherence-CE Memory Mesh the exclusive KV/prefix-cache data-plane boundary for LLM inference actors. vLLM and peer runtimes connect only to Coherence-CE supported APIs; Coherence-CE is backed by the coherent NAND block substrate: OpenZFS/NVMe-oF with DPU-handled RoCEv2 and cross-node mirrored vdevs where qualified.

## Context

The baseline package defined Mode K as an optional prefix-cache/KV workload tier and treated cross-node ZFS mirroring as experimental Mode X. The refresh corrects that maturity split: cross-node mirrored ZFS/NVMe-oF is a core requirement for the underlying coherent NAND block-storage tier, while Coherence-CE Memory Mesh is the service boundary above it. The RAG corpus reinforces that KV cache is not an ordinary file or block workload. It is request-shaped, model-versioned, token-position-sensitive, eviction-prone, and tightly coupled to LLM schedulers.

vLLM-style serving systems manage KV cache as paged blocks with block tables, sharing, preemption, and dynamic growth, but in this architecture they must not learn OpenZFS pools, DPU services, NVMe-oF namespaces, RoCEv2 classes, or RDMA memory details. They call Coherence-CE Memory Mesh through supported inference-facing APIs, including native REST, S3-object-style REST translation, or other approved destination protocols. Coherence-CE owns placement, hydration, replica selection, protocol translation, and persistence into the storage substrate. The OCP inference fabric profile reinforces that Coherence-CE mesh traffic, model-load traffic, storage-backend traffic, and background work must be isolated rather than treated as one converged flow.

## Decision

- Promote Coherence-CE Memory Mesh to the default active inference KV/prefix-cache service.
- Require every KV-cache client, including vLLM and peer runtimes, to connect to Coherence-CE only; clients must not bind to OpenZFS, DPU, NVMe-oF, RoCEv2, RDMA memory, or block-storage implementation details.
- Promote baseline Mode X terminology into a core gated coherent NAND block-storage requirement: cross-node ZFS mirrored vdevs over NVMe-oF/RDMA provide the durable block substrate below Coherence-CE after node-loss, fabric-loss, import, checksum, latency, and resilver gates pass.
- Store hot prefix/KV entries in Coherence-CE with identity fields for model, tokenizer, adapter, quantization profile, prompt-prefix hash, layer/head/block metadata, and data-layout version.
- Keep authoritative KV placement, replica state, API translation, hydration policy, and backing-store binding inside Coherence-CE. Do not use Redis alone as durable authority.
- Replicate hot KV entries at the Coherence-CE mesh layer across failure domains. The default policy is one primary plus one secondary; higher replication is workload-specific.
- Treat T0 accelerator memory as a runtime-local cache of active pages. Coherence-CE owns reusable prefix blocks, metadata, warm persistence, and backing-store recovery.
- Mark Coherence-CE mesh-to-storage, mesh replication, and rebuild traffic with ADR-004 fabric classes so model loads, RAG shard movement, and background re-indexing cannot starve the token path.
- Allow quantized KV formats only when the model/runtime profile has an acceptance gate for accuracy and latency.

## Data path

1. The inference gateway or runtime adapter normalizes request metadata and computes one or more prefix hashes.
2. vLLM or a peer runtime calls the Coherence-CE Memory Mesh endpoint through an approved client API such as native REST, S3-object-style REST translation, or another destination protocol exposed by the mesh.
3. Coherence-CE resolves model/tokenizer/adapter/profile compatibility, placement, replica state, and hydration policy internally.
4. On hit, Coherence-CE returns the correct KV/prefix payload or object reference in the client-facing protocol without exposing OpenZFS, DPU, NVMe-oF, RoCEv2, or RDMA state.
5. On miss, prefill computes the prefix state and publishes it back to Coherence-CE through the same mesh boundary.
6. Coherence-CE replicates, evicts, persists, or rebuilds entries according to request class and mesh policy.
7. Coherence-CE persists warm or durable state onto OpenZFS nodes; those nodes use DPU-handled NVMe-oF/RoCEv2 and cross-node mirrored vdevs below the mesh.

## Client and mesh boundary

| Boundary | Contract | Hidden implementation |
| --- | --- | --- |
| Inference runtime to Coherence-CE | REST, S3-object-style REST translation, or approved mesh protocol returns correct KV/prefix data | OpenZFS pool layout, DPU services, NVMe-oF namespaces, RoCEv2 fabric classes, RDMA memory registration |
| Coherence-CE to storage substrate | Mesh-owned persistence, hydration, replica, and rebuild operations | Cross-node mirrored ZFS vdev construction, DPU offload details, fabric path selection |
| Observability | Layer-tagged traces and metrics correlate runtime, Coherence-CE, storage, DPU, and fabric events | Client-facing APIs do not expose lower-layer control knobs |

## Key and layout policy

| Field | Requirement |
| --- | --- |
| `model_id` | Content-addressed model manifest, not human-readable alias only. |
| `tokenizer_id` | Explicit tokenizer version and vocabulary hash. |
| `adapter_id` | LoRA/adapter hash or `none`. |
| `runtime_profile` | Serving engine, attention implementation, block size, dtype, quantization, and GPU architecture. |
| `prefix_hash` | Hash of normalized token sequence and cache policy salt. |
| `block_index` | Logical block number compatible with paged KV management. |
| `placement_epoch` | Incremented when ownership or replicas change. |

## Replication and consistency

- KV entries are immutable after publication unless explicitly marked as extendable session state.
- Immutable prefix entries use write-once, read-many semantics and can be replicated without distributed locking on every read.
- Extendable session state uses a single writer per session and versioned append records.
- Coherence-CE metadata updates are quorum-protected. Data replication can be asynchronous for recomputable cache entries, but the mesh must identify incomplete replicas.
- A cache miss is allowed to recompute; a corrupt or wrong-version cache hit is not allowed to be served.
- Clients receive correctness and version compatibility from Coherence-CE responses, not from direct storage-layer inspection.

## Positive consequences

- Inference cache design follows LLM runtime behavior without forcing LLM state into a generic filesystem abstraction.
- vLLM and peer actors remain insulated from OpenZFS, DPU, NVMe-oF, RoCEv2, and RDMA implementation details.
- Cross-node durability work is below Coherence-CE and removed from the per-token client contract.
- KV-block compression, eviction, and placement can evolve inside Coherence-CE without changing OpenZFS pool layout or runtime client integrations.
- Cache locality becomes visible to the inference scheduler as Coherence-CE-provided health and locality signals.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Coherence-CE metadata becomes a bottleneck | Partition the keyspace inside the mesh, expose mesh metadata latency as an SLO, and avoid leaking placement control to clients. |
| Cache entries become semantically stale after model updates | Include model, tokenizer, adapter, dtype, quantization, and runtime profile in the key. |
| Quantization hurts answer quality | Gate each quantized profile with model-specific quality and long-context tests. |
| Recompute storms after node loss | Use replica-aware admission, hot-prefix prewarming, and rate-limited rebuild queues. |
| Cross-node mirror latency leaks into active decode | Keep active KV/decode state behind Coherence-CE service semantics; use the coherent NAND tier for backing, rebuild, persistence, and warm/cold recovery paths. |
| KV clients couple to storage internals | Enforce a Coherence-CE-only client contract and reject runtime integrations that require OpenZFS, DPU, NVMe-oF, RoCEv2, or RDMA awareness. |
| Coherence-CE rebuild traffic competes with gateway or model-load flows | Enforce ADR-004 traffic-class marking and ADR-007 admission limits for hydration, rebuild, and prewarm work. |

## Acceptance criteria

- A canary model can reuse a prefix cache entry across two workers through Coherence-CE without changing response semantics.
- A wrong model/tokenizer/adapter/profile cache entry is rejected by Coherence-CE key validation.
- Failure of one Coherence-CE mesh node causes reads to move to a mesh replica or recompute without corrupt cache responses.
- KV hydration p99 and prefix-cache hit ratio are exported by model, tenant, Coherence-CE endpoint, and backing tier.
- vLLM or peer runtime configuration contains only Coherence-CE endpoint/protocol credentials, not OpenZFS, DPU, NVMe-oF, RoCEv2, or RDMA configuration.
- The coherent NAND block substrate canary proves cross-node mirrored ZFS/NVMe-oF failure, import, checksum, latency, and resilver gates before it backs production-like inference data classes.
- Active decode canary tests show KV reuse/hydration does not synchronously depend on remote mirror acknowledgements for every token step.
- Coherence-CE mesh replication, hydration, persistence, and rebuild traffic are visible as distinct traffic classes in fabric and scheduler telemetry.

## Source documents

| ID | Use |
| --- | --- |
| A1, A2 | Existing Coherence-style prompt cache and KV-layer replication option. |
| R01 | PagedAttention, KV block tables, sharing, dynamic allocation, and preemption. |
| R02, R03 | LLM serving and scheduler metrics. |
| R25, R26, R27 | KV-cache quantization and vector quantization direction. |
| R15 | RDMA protocol choices for data exchange and memory management. |
| R34, R37 | OCP inference/training fabric profiles supporting separation of KV, model, storage, gateway, and background traffic. |

## Research update: CXL-backed KV remains Coherence-owned

The RAG refresh added CXL KV-cache research, including CXL-enabled processing-near-memory for 1M-token inference and rack-scale CXL shared-memory KV cache designs. These sources strengthen the case for CXL as a warm KV/prefix staging and memory-pressure relief tier, but they do **not** change the actor-facing contract: vLLM and peer inference runtimes continue to call Coherence-CE only. Coherence-CE owns any mapping to GPU HBM, host DRAM, CXL T1/T1.5, RDMA object paths, or OpenZFS-backed durability.

Acceptance addition: no vLLM adapter field, OpenAI-compatible extension, or scheduler request may expose CXL device identifiers, OpenZFS vdevs, RDMA QPs, DPU queues, or NVMe-oF namespace details as required API inputs.
