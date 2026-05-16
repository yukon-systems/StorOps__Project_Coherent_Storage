# ADR-010: Coherence-CE Write Policy to OpenZFS

**Project:** Project Coherent Storage  
**Version:** 2026-Q2  
**Package:** v2 inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Use a class-based Coherence-CE write policy to OpenZFS. Coherence-CE owns all KV/prefix-cache writes, acknowledgements, replay, and promotion. OpenZFS/NVMe-oF provides the durable NAND block substrate below Coherence-CE; vLLM and peer inference actors never choose or observe OpenZFS datasets, zvols, pools, DPU paths, NVMe-oF namespaces, RoCEv2 classes, or RDMA memory details.

## Context

ADR-002 makes Coherence-CE Memory Mesh the exclusive KV/prefix-cache boundary. ADR-006 makes cross-node mirrored OpenZFS/NVMe-oF the core durable NAND substrate. The missing decision is how Coherence-CE decides whether a KV mutation is acknowledged from mesh memory, queued for background persistence, or held until OpenZFS has accepted a durable write.

Oracle Coherence documentation distinguishes write-through behavior, where a cache update completes only after the backing store update succeeds, from write-behind behavior, where modified entries are queued and asynchronously written to the backing store after a delay. It also stresses idempotent backing-store operations because write-through and write-behind operations may be retried during failover. Coherence persistence documentation adds active/on-demand persistence and snapshot concepts, but the Project Coherent Storage layering keeps OpenZFS as the durable backing substrate beneath Coherence-CE rather than exposing OpenZFS to inference clients.

OpenZFS documentation makes the durability boundary explicit: the `sync` dataset property controls synchronous request behavior; `standard` honors synchronous requests, `always` forces every transaction through sync semantics with a performance penalty, and `disabled` is dangerous because it ignores application sync demands. OpenZFS scrub/resilver and ZIO scheduling documentation also show that durability maintenance has measurable latency consequences and must feed admission control.

## Decision

- Make write policy a property of the KV durability class, not a cluster-wide switch.
- Use **write-around** for active decode state that is per-token critical and recomputable.
- Use **write-back/write-behind** for reusable prefix KV that is valuable but recomputable.
- Use **write-through** for warm durable prefix, session checkpoint, audit, compliance, and externally promised durable state.
- Return durability state explicitly from Coherence-CE: `volatile`, `mesh_committed`, `writeback_pending`, `durable`, `degraded`, or `rejected`.
- Never let vLLM select OpenZFS sync modes, SLOG devices, zvols, NVMe-oF targets, DPU paths, or fabric classes.
- Never acknowledge a durable class as `durable` until Coherence-CE has evidence from the backing-store adapter that the write has crossed the required OpenZFS durability boundary.
- Treat host-mediated storage fallback as degraded resilience. DPU/SmartNIC hardware remains the normal required storage-path hardware for NVMe-oF/RoCEv2 offload and RDMA resource mediation.

## Write policy by durability class

| KV class | Default write policy | Client-visible success condition | Backing-store behavior | Scheduler consequence |
| --- | --- | --- | --- | --- |
| KV-D0 active volatile decode | Write-around | Active runtime accepts in-flight state | No OpenZFS write | Admit only while accelerator/host memory budget exists |
| KV-D1 mesh-replicated recomputable | Mesh write-through only | Coherence-CE primary plus configured mesh replica commit | No default OpenZFS write; optional spill is advisory | Recompute allowed on loss |
| KV-D2 write-back reusable prefix | Mesh commit plus bounded write-back | Coherence-CE quorum/replica commit; response says `writeback_pending` until durable | Idempotent async write-behind queue to OpenZFS-backed object/block service | Admit while durable lag stays below class threshold |
| KV-D3 write-through warm prefix | Write-through | Coherence-CE commit plus OpenZFS-backed durable ack | Synchronous durable write through backing-store adapter | Queue/throttle if durable p99 or pool health is outside SLO |
| KV-D4 extendable session/checkpoint | Versioned write-through checkpoints; optional write-back tail | Single-writer epoch recorded; checkpoints durable before advertised | Append/version log and periodic checkpoint to OpenZFS | Require fencing, epoch monotonicity, and recovery budget |
| KV-D5 governed/audit/compliance | Write-through plus snapshot/retention | Durable write and retention metadata accepted | Durable dataset/object path, retention/snapshot policy, audit trace | Fail closed when durability evidence is missing |

## Coherence-CE write pipeline

1. The vLLM adapter calls Coherence-CE with model, tokenizer, adapter, runtime profile, prefix/block identity, requested durability class, idempotency key, and payload reference.
2. Coherence-CE validates key compatibility and rejects any stale or wrong-version state before placement.
3. Coherence-CE selects the write policy from the durability class and tenant/SLO policy.
4. For KV-D0, Coherence-CE records no durable obligation.
5. For KV-D1, Coherence-CE commits to the configured mesh replicas and marks the object recomputable.
6. For KV-D2, Coherence-CE commits to mesh replicas, appends an idempotent write-behind record, and returns `writeback_pending` until the backing store confirms durability.
7. For KV-D3 through KV-D5, Coherence-CE sends the write through the backing-store adapter and returns success only when the durability class's backing-store condition is met.
8. Coherence-CE emits per-write metrics for ack latency, durability lag, queue age, backing-store latency, failure class, and rejected stale/incompatible writes.

## OpenZFS backing policy

| Backing dataset or object family | Allowed KV classes | Required OpenZFS posture |
| --- | --- | --- |
| `coherence-kv-spill` | KV-D2 | `sync=standard` unless class profile explicitly marks recomputable loss; no durable ack until flush evidence exists |
| `coherence-prefix-durable` | KV-D3 | `sync=standard`; mirrored low-latency log device where sync latency requires it; snapshots optional by retention policy |
| `coherence-session-checkpoints` | KV-D4 | `sync=standard` or `sync=always` for explicitly strict profiles; versioned append/checkpoint layout; rollback-safe snapshots |
| `coherence-governed-kv` | KV-D5 | `sync=standard` or stricter; snapshots/retention; audit trace; no `sync=disabled` |
| `coherence-rebuild-journal` | KV-D2 through KV-D5 | Idempotent records, bounded replay window, checksum validation |

`sync=disabled` is forbidden for KV-D3 through KV-D5 and forbidden anywhere Coherence-CE advertises `durable`. If it is used for a lab-only recomputable spill profile, the class must remain KV-D2 or lower and scheduler admission must treat the data as rebuildable, not durable.

## Write-back controls

Coherence-CE write-back queues must expose:

- oldest pending record age;
- pending bytes and records by tenant, model, prefix shard, and durability class;
- retry count and last failure reason;
- idempotency-key replay count;
- backing-store commit p50/p95/p99;
- durable lag from mesh commit to OpenZFS durable ack;
- high-watermark state used by scheduler admission.

Write-back may coalesce repeated updates only for immutable or superseded prefix objects whose identity includes a monotonic epoch or content hash. KV-D4 and KV-D5 must not use lossy coalescing; if coalescing is needed for performance, the natural key must include a version or sequence so audit/recovery semantics remain explicit.

## Positive consequences

- Active decode does not pay OpenZFS mirror latency on every token.
- Recomputable KV can use write-back for performance without being misrepresented as durable.
- Durable prefix/session/audit data uses OpenZFS integrity and operational tooling intentionally.
- Scheduler admission can reason about durable lag instead of treating all cache hits as equivalent.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Write-back queue loss loses reusable prefix data | KV-D2 remains recomputable; queue state is replicated and replayed but loss degrades hit rate, not correctness. |
| Durable classes inherit unsafe dataset tuning | Block KV-D3 through KV-D5 promotion unless dataset policy forbids `sync=disabled` and reports pool/log health. |
| OpenZFS scrub/resilver harms inference p99 | Feed ZIO/scrub/resilver state into ADR-014 scheduler admission and throttle background persistence. |
| Write-through creates cross-entry partial commits | Use idempotent records, per-object durability, and explicit multi-object manifest commit; do not imply distributed two-phase commit across independent stores. |
| DPU fallback is mistaken as normal mode | Mark host fallback as degraded, emit fallback metrics, and require DPU readiness for production-like storage-path admission. |

## Acceptance criteria

- Every Coherence-CE publish request resolves to exactly one write policy derived from durability class and tenant/SLO policy.
- KV-D0/KV-D1 canaries prove no synchronous OpenZFS write is needed on the active token path.
- KV-D2 canary exposes `writeback_pending`, durable lag, and recompute behavior after write-back loss.
- KV-D3/KV-D4/KV-D5 canaries fail closed or queue when OpenZFS durable ack evidence is unavailable.
- Dataset policy validation rejects `sync=disabled` for any class advertised as durable.
- vLLM adapter configuration contains only Coherence-CE endpoints, credentials, and API fields.
- Scheduler admission changes from GREEN to AMBER/RED when write-back queue age, durable lag, or OpenZFS pool/log health violates policy.

## Source documents

| ID | Use |
| --- | --- |
| A1, A2 | Coherence-style prompt cache and KV-layer replication above coherent NAND. |
| R01, R02, R03 | vLLM KV memory behavior and scheduler pressure from KV/cache state. |
| R04, R21, R22, R23 | ML I/O patterns and OpenZFS integrity/performance considerations. |
| R05, R06, R07, R15 | RDMA/object/DPU backing-store and data-path concerns below Coherence-CE. |
| O01 | Coherence read-through, write-through, write-behind, write-behind queue, and idempotent CacheStore guidance. |
| O02 | Coherence active/on-demand persistence and snapshot posture. |
| O04, O05, O06, O07 | OpenZFS sync property, log device, scrub/resilver, and ZIO scheduler behavior. |
