# ADR-001: Inference Storage Principles and SLOs

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Optimize Project Coherent Storage for LLM inference by separating hot KV state, model/object data, RAG/vector data, checkpoint/artifact data, and control state into latency-scoped storage tiers with LLM-visible service-level objectives.

## Context

The baseline architecture established the rack, fabric, OpenZFS/NVMe-oF, DPU, Xen, heterogeneous compute, and observability foundation. It treated LLM prompt/KV cache as an optional workload tier. The RAG research corpus shifts the priority: LLM inference is constrained by KV-cache capacity, model residency, small random reads, vector lookup latency, and fabric tail behavior as much as by raw storage throughput.

The 2026 OCP additions broaden the SLO envelope beyond server-local storage. AI data-center power, rack-integrated energy storage, HVDC/LVDC shelves, timing validation, and OCP cluster reference architectures make facility readiness, clock quality, rack power headroom, and lifecycle observability part of the admission baseline rather than background assumptions.

CXL and PMem evidence changes the host-memory tier from a generic capacity note into a governed hardware decision. CXL can extend memory on heterogeneous non-Intel platforms and in AIC, U.3-class, and EDSFF packaging, but it is not local DRAM and must be placed close to the consuming CPU/DPU/GPU root complex. Optane PMem 200/300-class systems remain useful persistent-memory references, but their CPU/board generation coupling makes CXL the preferred forward-looking expansion tier when topology and telemetry qualify.

The target workload has several distinct paths:

- Interactive inference needs low Time To First Token (TTFT), low Time Per Output Token (TPOT), and stable p99 cache hydration latency through the Coherence-CE Memory Mesh API boundary.
- Batch inference and embedding jobs need throughput, prefetching, and checkpoint/artifact durability.
- RAG services need high-fanout vector/index lookups plus immutable corpus chunk reads.
- Long-context inference needs KV-cache memory efficiency, quantization, eviction, and tiered hydration.
- Accelerator nodes need data paths that avoid unnecessary CPU copies when GPUDirect-style paths are supported.

## Decision

- Treat inference storage as a multi-tier system, not as one shared block/file store.
- Make Coherence-CE Memory Mesh the sole KV/prefix-cache service boundary for inference actors such as vLLM.
- Keep durable OpenZFS/NVMe-oF storage, DPU offload, and RoCEv2 details behind the Coherence-CE, model/object, and storage service layers rather than directly in every inference request.
- Make TTFT, TPOT, cache-hit ratio, KV hydration latency, model load time, vector lookup p99, and fabric queue health first-class SLO signals.
- Keep baseline dual RoCEv2 fabrics and edge-control governance, but add inference-specific admission gates before workloads are placed on GPU, NPU, FPGA, or CPU hosts.
- Treat rack power envelope, PSU/power-shelf health, ESS/backup posture, power quality, and time-synchronization readiness as SLO-adjacent platform signals for inference placement and rollout.
- Treat CXL/PMem as governed host-memory tiering inputs: CXL is a T1/T1.5 warm-memory expansion candidate only when role, persistence semantics, NUMA/root-complex placement, switch/bifurcation state, and telemetry are recorded.

## Storage tiers

| Tier | Name | Primary location | Intended data | Durability | Latency posture |
| --- | --- | --- | --- | --- | --- |
| T0 | Accelerator memory | GPU HBM, accelerator SRAM/HBM | Active KV pages, in-flight decode buffers, current batch state | Volatile | Per-token critical path |
| T1 | Host hot memory | Host DRAM | Prefix metadata, hot KV blocks, vector index heads, model routing state | Replicated or rebuildable | Sub-millisecond target |
| T1.5 | Governed host memory expansion | CXL Type-3 memory, persistent CXL, or Optane PMem where qualified | Warm prefix/KV staging, Coherence metadata, vector heads, object metadata, write-back buffers, ARC/page-cache capacity under budget | Role-specific; volatile unless persistence is proven | Between local DRAM and T2; topology-sensitive |
| T2 | Node-local fast NVMe | Local NVMe, OpenZFS datasets/zvols | Warm KV blocks, model shards, hot RAG chunks, write-ahead cache | Local ZFS redundancy plus replica policy | Low millisecond p99 target |
| T3 | RDMA object/block tier | RDMA-first object store, NVMe-oF namespaces, DPU/SPDK targets | Model weights, corpus chunks, adapters, checkpoints, batch artifacts | Durable replicated tier | Throughput and bounded p99 |
| T4 | Cold archive | QLC/HDD/object archive | Old corpora, retired models, logs, compliance copies | Durable | Not in online inference path |

## Data-class policy

| Data class | Required behavior | Default tiering |
| --- | --- | --- |
| Active decode KV | Must not block on durable storage during token generation | T0 only, with eviction metadata in T1 |
| Reusable prefix KV | Must hydrate quickly and preserve block identity across requests through Coherence-CE APIs | Coherence-CE Memory Mesh owns T1/T1.5/T2/T3 placement and persistence |
| Model weights and adapters | Immutable, content-addressed, versioned, prefetchable | T2/T3 with manifest and checksum |
| RAG corpus chunks | Immutable, chunked, deduplicated, re-indexable | T3 primary, T2 hot chunks |
| Vector indexes | Versioned by embedding model and corpus snapshot | T1/T2 hot index, T3 durable build artifacts |
| Checkpoints and batch outputs | Durable and resumable, not per-token critical | T3/T4 |
| Control and audit state | Strongly consistent desired state and immutable audit | baseline control plane, outside inference data path |

## SLO baseline

| Objective | SLI | lab target |
| --- | --- | --- |
| Interactive first-token latency | `ttft_p95_ms`, `ttft_p99_ms` | Baseline per model, then enforce no regression above 10% during storage changes |
| Decode latency | `tpot_p95_ms`, `tpot_p99_ms` | Baseline per model and batch profile |
| Prefix cache effectiveness | `prefix_cache_hit_ratio` | Workload-specific target; alert on sustained regression |
| KV hydration latency | `kv_hydrate_p99_ms` | <= 2 ms for T1/T2 hits after baseline tuning |
| Model warm load | `model_weight_load_p99_s` | Bounded by model class; must support prefetch before admission |
| RAG vector lookup | `vector_lookup_p99_ms` | Baseline per index size and recall target |
| RDMA fabric loss | `rdma_priority_discards` | 0 sustained drops in validation windows |
| Storage path availability | `inference_data_path_available` | >= 99.5% during lab service windows |
| Rack/facility readiness | `rack_power_headroom`, `psu_shelf_health`, `ess_backup_ready`, `power_quality_state` | Recorded before canary admission; no interactive promotion on unknown state |
| Timing readiness | `clock_error_state`, `boundary_clock_health`, `holdover_test_state` | Recorded for fabric and request-trace correlation before multi-rack rollout |
| Host memory tier readiness | `cxl_latency_p99_ms`, `cxl_pressure`, `cxl_topology_state`, `cxl_error_state`, `arc_cxl_budget_state` | CXL/PMem tier use is blocked or class-limited when topology, freshness, or p99 latency is unknown |

## Positive consequences

- Storage decisions are tied to LLM user-visible behavior instead of only fio or link-speed metrics.
- The architecture can tune hot KV, model delivery, RAG retrieval, and durable artifacts independently.
- OpenZFS remains valuable for integrity and operations while Coherence-CE hides durable-storage mechanisms from inference clients and keeps avoidable durability latency out of active decode.
- The scheduler can make explicit trade-offs between low-latency interactive work and high-throughput batch work.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Too many tiers add operational complexity | Define strict data-class ownership and keep movement between tiers observable. |
| Hot KV tier loses data during failures | Treat KV as recomputable cache unless a workload explicitly requires durable prefix state; Coherence-CE owns mesh-level replication and backing-store recovery. |
| Model and corpus versions drift | Use content-addressed manifests and make model/corpus/index versions part of request admission. |
| SLOs become aspirational | Make promotion depend on benchmark and telemetry evidence from ADR-009. |
| Facility, power, or timing constraints are invisible to inference admission | Add rack power, PSU/power-shelf, ESS, power-quality, and timing state to source-of-truth and rollout gates. |
| CXL capacity is treated as generic DRAM | Govern CXL as T1/T1.5 with role, persistence, topology, NUMA, switch/bifurcation, latency, and telemetry evidence before admission. |

## Acceptance criteria

- A source-of-truth schema identifies the tier, owner, replication policy, and SLO class for each inference data class, including CXL/PMem role, CPU socket/root complex, NUMA node, switch/bifurcation state, and telemetry endpoint when T1.5 is used.
- A representative inference request can be traced across model manifest lookup, optional RAG retrieval, Coherence-CE KV lookup/hydration, GPU execution, and Coherence-CE write-back.
- TTFT, TPOT, Coherence-CE KV hydration, model-load, vector-lookup, RDMA, DPU, ZFS, and cache-hit metrics appear in one dashboard with clear layer ownership.
- Workload admission can reject a request because of storage or fabric SLO state, not only because of GPU availability.
- Rack and facility metadata record power envelope, PSU/power-shelf profile, ESS/backup posture, timing profile, and telemetry freshness before an inference canary is promoted.

## Source documents

| ID | Use |
| --- | --- |
| A0, A1, A2 | Baseline topology, fabric, OpenZFS/NVMe-oF, and KV-cache design options. |
| R01, R02, R03 | KV-cache pressure, LLM serving metrics, and scheduling implications. |
| R04, R21 | ML/HPC I/O patterns, burst buffers, caching, and storage hierarchy. |
| R25, R26, R27 | KV/vector quantization direction for memory-efficient hot tiers. |
| R28, R29, R79, R83, R84, R85, R138 | Far-memory, CXL/PMem tiering, and Optane PMem/SSD reference behavior. |
| R31, R35, R36, R41, R42 | Facility power, rack energy-storage, HVDC/LVDC, power-quality, and AI data-center readiness constraints. |
| R32, R34, R37 | Timing validation and OCP inference/training cluster profiles that make platform readiness part of SLO governance. |
| O10, O11, O12, O13 | Official CXL and Optane PMem references used for CXL-vs-Optane hardware intent and placement governance. |

