# ADR-011: KV Durability Classes

**Project:** Project Coherent Storage  
**Version:** 2026-Q2  
**Package:** v2 inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Define six KV durability classes, KV-D0 through KV-D5, that tell Coherence-CE how to acknowledge, replicate, persist, recover, evict, and admit KV/prefix-cache state. Durability class is the only vLLM-visible durability knob; lower storage, DPU, RDMA, and fabric mechanics remain hidden behind Coherence-CE.

## Context

LLM KV cache is not one data type. Active decode state is latency-critical and usually recomputable only by rerunning the request. Reusable prefix KV is valuable because it reduces TTFT and prefill cost, but many prefix entries remain functionally recomputable from model, tokenizer, adapter, prompt, and runtime profile. Long sessions, checkpoints, governed workloads, and audit traces have stronger recovery and retention requirements.

The architecture therefore needs explicit durability classes instead of implicit cache labels such as hot, warm, and cold. These classes let Coherence-CE select write-around, write-back, or write-through behavior and let the scheduler admit work with known loss/recompute semantics.

## Decision

- Make durability class mandatory on every Coherence-CE KV publish or derive it from an explicit tenant/model policy.
- Keep active per-token state out of OpenZFS unless promoted by an explicit Coherence-CE operation.
- Preserve semantic identity in every KV key: model, tokenizer, adapter, runtime profile, layout version, prefix hash, logical block index/range, and placement epoch.
- Reject stale or incompatible KV as a miss or hard error; never serve wrong KV.
- Use durability class to drive storage policy, mesh replication, TTL, eviction priority, scheduler admission, and failure response.

## Durability classes

| Class | Name | Intended data | Ack policy | Persistence policy | Default TTL/retention | Loss/recovery semantics |
| --- | --- | --- | --- | --- | --- | --- |
| KV-D0 | Active volatile decode | Current batch decode pages, transient speculative state | Runtime-local/mesh transient ack only | None; write-around | Request lifetime | Request fails, retries, or recomputes from prompt; no cross-request promise |
| KV-D1 | Mesh-replicated recomputable | Hot prefix blocks likely reused soon | Coherence primary plus one mesh replica by default | None by default; optional advisory spill | Minutes to hours | Loss becomes cache miss; recompute is allowed and expected |
| KV-D2 | Write-back reusable prefix | High-value reusable prefixes, quantized KV variants, hot long-context chunks | Mesh quorum or configured replica policy; durable state may be pending | Bounded write-back/write-behind to OpenZFS-backed tier | Hours to days | If not durable, loss becomes recompute; if durable, hydrate from backing tier |
| KV-D3 | Write-through warm prefix | Expensive-to-prefill shared prefixes, approved system prompts, model-specific warm cache | Mesh commit plus durable backing-store ack | Write-through to OpenZFS-backed tier | Days to release window | Serve from mesh or hydrate; block/queue publishes when durability unavailable |
| KV-D4 | Extendable session/checkpoint | Long-running sessions, resumable agent work, batch checkpoint state | Single-writer epoch plus durable checkpoint ack | Versioned append/checkpoint records; optional write-back tail only if recomputable | Session policy | Recover to last durable epoch; reject ambiguous writers |
| KV-D5 | Governed/audit/compliance | Regulated prompts, audit KV, reproducibility bundles, compliance copies | Durable ack plus retention/audit metadata | Write-through plus snapshot/retention policy | Policy-defined | Fail closed if durability, retention, or provenance evidence is missing |

## Class-derived policy fields

Each class resolves to these concrete policy fields inside Coherence-CE:

| Field | Meaning |
| --- | --- |
| `min_mesh_replicas` | Minimum in-mesh copies before mesh ack. |
| `ack_mode` | `transient`, `mesh_committed`, `writeback_pending`, or `durable`. |
| `backing_policy` | `none`, `advisory_spill`, `write_back`, `write_through`, or `write_through_retained`. |
| `max_durable_lag_ms` | Maximum time from mesh commit to durable ack before scheduler changes admission. |
| `ttl_seconds` | Maximum normal retention absent explicit refresh/promotion. |
| `eviction_priority` | Relative protection against memory/cache eviction. |
| `recompute_allowed` | Whether loss may be treated as miss/recompute. |
| `fencing_required` | Whether single-writer epoch and split-brain fencing are mandatory. |
| `snapshot_required` | Whether OpenZFS/object snapshots or retention manifests are mandatory. |

## Promotion and demotion

Coherence-CE may promote or demote data only through explicit policy:

- KV-D0 may be promoted to KV-D1 or KV-D2 after prefill if the adapter publishes reusable prefix blocks.
- KV-D1 may be promoted to KV-D2 when reuse probability or prefill cost crosses policy thresholds.
- KV-D2 may be promoted to KV-D3 only after backing-store durability is confirmed and class metadata is updated.
- KV-D3 may be demoted to KV-D2 after model/corpus/runtime expiry if recompute remains acceptable.
- KV-D4 may not be demoted below the last advertised durable checkpoint.
- KV-D5 may not be demoted until retention policy permits it.

Promotions and demotions are metadata operations in Coherence-CE. They do not expose OpenZFS or fabric details to vLLM.

## Scheduler admission coupling

| Class | GREEN admission | AMBER admission | RED admission |
| --- | --- | --- | --- |
| KV-D0 | Admit if local memory and token SLO fit | Admit with lower concurrency or preemption risk noted | Reject/queue if memory unsafe |
| KV-D1 | Admit if mesh replicas healthy | Admit with recompute budget | Recompute or miss; do not rely on hit |
| KV-D2 | Admit if durable lag and queue age below threshold | Admit reads; throttle/promote writes | Treat pending writes as recomputable; stop new write-back growth |
| KV-D3 | Admit if backing tier healthy | Queue/throttle publishes; reads may continue from durable replicas | Reject/queue durable publishes |
| KV-D4 | Admit with valid writer epoch and checkpoint budget | Allow reads; restrict new writers | Fence/stop ambiguous writers |
| KV-D5 | Admit only with full durability/retention evidence | Queue; no degraded durable promise | Fail closed |

## Positive consequences

- Operators can reason about loss and recovery behavior before enabling a workload.
- vLLM integrations remain simple: they select or inherit a durability class and rely on Coherence-CE for the rest.
- Scheduler policy can distinguish cache miss cost from correctness risk.
- OpenZFS write pressure is reserved for data classes that benefit from durable backing.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Tenants overuse high durability classes | Apply quotas, per-class pricing/cost accounting, and scheduler admission limits. |
| Operators mislabel non-recomputable state as KV-D2 | Require tenant/model policy approval before write-back classes can be used for non-default workloads. |
| KV identity misses a compatibility dimension | Include model, tokenizer, adapter, runtime profile, layout version, quantization, and block geometry in every key. |
| Promotions create stale durable state | Promotions require epoch checks and content-hash validation. |
| Quantized KV changes answer quality | Gate quantized profiles with quality tests and versioned runtime profiles. |

## Acceptance criteria

- Every Coherence-CE KV object has exactly one durability class.
- Class policy resolves deterministically to ack mode, backing policy, TTL, eviction priority, and failure behavior.
- A wrong model/tokenizer/adapter/runtime/profile KV entry is rejected before serving.
- KV-D2 loss drill produces recompute/miss behavior, not corrupted response behavior.
- KV-D3 through KV-D5 durable ack drills prove backing-store evidence exists before success is returned.
- Scheduler admission dashboards show class-specific admission, throttling, rejection, and recompute reasons.

## Source documents

| ID | Use |
| --- | --- |
| R01 | vLLM/PagedAttention KV block identity, sharing, memory pressure, and preemption. |
| R02, R03, R30 | Scheduler and inference-serving SLO pressures. |
| R25, R26, R27 | Quantized KV/vector formats requiring compatibility and quality gates. |
| R04, R21, R22, R23 | Storage hierarchy and OpenZFS operational behavior by data class. |
| O01, O02 | Coherence write-through/write-behind and persistence foundations. |
| O04, O06, O07 | OpenZFS sync and maintenance behavior that durability classes must account for. |
