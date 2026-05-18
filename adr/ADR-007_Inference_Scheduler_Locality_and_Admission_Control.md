# ADR-007: Inference Scheduler Locality and Admission Control

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Make the inference scheduler storage-aware through service-level signals. Admission and placement must consider model residency, Coherence-CE KV/prefix locality, RAG index locality, fabric/storage health, accelerator memory pressure, and request SLO class before work is accepted, without requiring inference runtimes to know lower storage layers.

## Context

The baseline architecture used rack and fabric locality for heterogeneous compute placement. The RAG corpus shows that LLM inference is not just accelerator scheduling. TTFT and TPOT depend on model load state, KV-cache pressure, batching, preemption, memory fragmentation, data movement, and retrieval latency. A request placed on an idle accelerator can still miss its SLO if the model is cold, prefix blocks are remote, vector indexes are overloaded, or fabric congestion delays hydration.

The scheduler therefore becomes the coordination point between inference runtime state and service-level storage state. For KV/prefix cache, the scheduler consumes Coherence-CE mesh locality, endpoint health, and SLO signals rather than direct OpenZFS, DPU, QAT, NVMe-oF, RoCEv2, or RDMA placement data from inference runtimes. The OCP inference/training fabric RAs and AI data-center whitepaper extend that coordination point to cluster profile, tenant gateway, fabric lifecycle, power headroom, and facility telemetry.

## Decision

- Use a global control-plane scheduler for policy, quotas, model placement, and admission.
- Use local worker/runtime schedulers for token batching, KV block allocation, eviction, and preemption.
- Feed scheduler decisions with service-owned telemetry from Coherence-CE, model/object, RAG, storage, and fabric layers, not just accelerator availability.
- Admit interactive requests only when the selected placement can satisfy the request's SLO envelope with current model, Coherence-CE KV, RAG, fabric, and queue state.
- Prefer request placement where the model is already resident and Coherence-CE reports the prefix/KV data as local, replicated, or cheaply hydratable.
- Keep proactive work, batch embedding jobs, re-indexing, checkpoint movement, model warmup, and corpus ingest below interactive inference priorities.
- Record every placement decision with the inputs used, the expected SLO, and the actual outcome.
- Include OCP cluster profile, tenant gateway path, rack power headroom, timing/telemetry freshness, and facility constraints in placement decisions when they affect data-path viability.
- Include QAT device/service/PF/VF trust and fallback state when crypto/compression acceleration participates in the selected service path.
- Include CXL tier state, CPU/root-complex locality, NUMA distance, switch hop count, bifurcation state, and CXL latency/pressure in placement decisions when Coherence-CE, OpenZFS, DPU, or GPU paths consume CXL.

## Placement inputs

| Input | Examples | Why it matters |
| --- | --- | --- |
| Model residency | Model ID, version, adapter, tokenizer, quantization, GPU memory footprint | Cold model loads dominate TTFT. |
| Coherence-CE KV/prefix locality | Prefix hash, mesh endpoint, replica health, hydration policy, API latency | Prefix reuse is a first-order performance signal, but storage internals remain hidden behind Coherence-CE. |
| RAG locality | Embedding model, index shard, corpus version, hot chunk replicas | Retrieval delay adds directly to TTFT. |
| Accelerator state | GPU/HBM free space, active sequences, batch state, preemption pressure | KV growth can force eviction or recompute. |
| Host memory state | DRAM pressure, pinned memory, runtime allocator pressure | Hydration and staging paths need bounded memory. |
| CXL tier/topology state | CXL capacity/pressure, root complex, NUMA node, switch hop count, bifurcation state, link width/speed, p99 latency, error/thermal state | CXL can improve warm tiers but bad placement can break TTFT/TPOT and DPU/GPU staging. |
| Storage service state | Coherence-CE backing-tier latency, object/model tier latency, queue depth, substrate health summaries | Warm and durable tiers affect cache miss behavior without becoming runtime-client concerns. |
| Fabric state | Rack, rail, fabric plane, ECN/CNP, PFC, drops, RTT | Congestion can invalidate a good compute placement; details are consumed by control services, not vLLM. |
| DPU state | Firmware profile, queues, CPU/memory, offload service health | DPU failure or saturation changes data-path latency below the Coherence-CE/storage boundary. |
| QAT state | Device/driver/firmware version, PF/VF ownership, trusted-assignment state, endpoint/reset/error state, service health, CPU fallback | QAT can accelerate crypto/compression paths, but endpoint or VF/PF faults affect placement only through service-owned summaries. |
| Tenant/SLO class | Interactive, background, batch, system, maintenance | Admission must protect higher-value latency classes. |
| Cluster/facility profile | OPG/XOC profile, tenant gateway path, rack power headroom, timing state, cooling/power constraints | A technically idle accelerator can still be inadmissible if its fabric or facility envelope is unsafe. |

## Scheduling model

The scheduler uses a two-stage decision:

1. Filter candidates that cannot satisfy correctness, security, model compatibility, fabric reachability, or tenant policy.
2. Score remaining candidates using a weighted locality and risk function.

Candidate scoring must favor:

- Resident model and adapter.
- Local or same-rack Coherence-CE prefix/KV availability.
- Local vector-index shard or low-latency replicated shard.
- Healthy fabric plane with low ECN/CNP/PFC pressure.
- Available accelerator memory for expected KV growth.
- Lower preemption risk for long-context requests.
- Storage tiers that are below p99 latency thresholds.
- Qualified same-root-complex CXL for warm Coherence/OpenZFS-adjacent roles when it reduces DRAM pressure without increasing tail latency.

The score must penalize:

- Cold model loads in the interactive path.
- Remote Coherence-CE hydration during active congestion.
- RAG shard fanout across congested fabric links.
- DPU, NVMe-oF, or ZFS degradation.
- QAT endpoint/VF/PF/service degradation when a selected service path depends on QAT acceleration and CPU fallback is not qualified.
- Eviction of high-reuse prefixes.
- Mixing proactive jobs with interactive SLO pressure.
- Placing work on a rack or fabric profile with insufficient power, timing, telemetry, or gateway health evidence.
- Using CXL hidden behind switch layers, oversubscribed auto-bifurcation, cross-socket access, or stale CXL telemetry for latency-sensitive roles.

## Admission and degradation

The scheduler may reject, queue, degrade, or reroute work when SLOs cannot be met.

Allowed degradation actions:

- Route to a lower-latency model replica with the same model contract.
- Use a smaller context window only when the calling service allows it.
- Disable optional retrieval expansion while preserving required retrieval.
- Serve from a lower-recall but prequalified vector index only for explicitly allowed tenants.
- Queue proactive work behind interactive work.
- Trigger model warmup or index replica creation before accepting more traffic.
- Demote a CXL-expanded placement to local DRAM, recompute, or queue when CXL topology or latency is AMBER for the requested class.
- Demote a QAT-assisted crypto/compression path to CPU fallback, throttle, or queue when QAT endpoint/VF/PF state is AMBER and fallback SLO is known.

Disallowed degradation actions:

- Serving from mismatched model, tokenizer, adapter, embedding, or corpus versions.
- Serving stale vector results without version compatibility.
- Reusing KV blocks across incompatible runtime or tokenization state.
- Silently bypassing tenant isolation or data residency policy.

## Queue and preemption policy

- Interactive decode steps have priority over model warmup, corpus ingest, re-indexing, and checkpoint/artifact movement.
- Long-context requests must reserve expected KV growth or accept explicit preemption/recompute policy before admission.
- Prefix blocks with high reuse probability should be protected from eviction.
- Eviction policy must distinguish recomputable KV/cache data from durable model/corpus/index data.
- Batch jobs and proactive agent work should run only inside explicitly budgeted background windows or on isolated capacity.

## Positive consequences

- Accelerator utilization improves without hiding storage and fabric tail latency.
- TTFT and TPOT become schedulable outcomes rather than after-the-fact measurements.
- Cache locality becomes a first-class placement input.
- Interactive inference is protected from background ingest, re-indexing, and artifact movement.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Scheduler becomes too complex to reason about | Start with a small input set and require decision logs for every admitted request. |
| Telemetry lag causes bad placement | Include telemetry freshness in candidate scoring and fall back to conservative admission. |
| High locality preference causes imbalance | Add fairness and saturation penalties by worker, rack, rail, and tenant. |
| Rejections harm availability | Provide explicit queue/degrade/reroute policies and autoscale/warmup triggers. |
| Facility or gateway constraints are invisible to placement | Feed rack power, gateway, OCP cluster profile, Coherence-CE endpoint health, and timing/telemetry freshness into the same decision log as storage/fabric state. |
| QAT acceleration is treated as transparent | Score QAT only through service summaries that include trust scope, PF/VF ownership, endpoint health, reset state, and CPU fallback evidence. |
| CXL improves capacity but worsens locality | Score CXL separately from DRAM; penalize cross-socket, switched, auto-bifurcated, thermally throttled, or telemetry-stale CXL. |

## Acceptance criteria

- A request placement record includes model residency, Coherence-CE KV locality, RAG locality, fabric state, storage service state, accelerator memory, and SLO class.
- A cold model load is not admitted into the interactive SLO class unless the configured TTFT budget permits it.
- A synthetic prefix-reuse benchmark shows higher placement preference for workers holding matching prefix/KV blocks.
- A vector-index degradation drill causes admission throttling or rerouting rather than unbounded tail latency.
- Background re-indexing and checkpoint movement cannot starve interactive KV hydration.
- Scheduler dashboards expose admission, rejection, reroute, warmup, eviction, preemption, QAT endpoint/VF/PF/fallback, CXL topology/pressure, power/facility, gateway, and telemetry-freshness reasons.

## Source documents

| ID | Use |
| --- | --- |
| A0 | Existing rack/fabric locality and heterogeneous compute baseline. |
| R01 | KV block allocation, sharing, preemption, and memory pressure in LLM serving. |
| R02 | LLM inference scheduler control-plane and data-plane responsibilities. |
| R03 | TTFT/TPOT definitions and HPC inference/RAG serving patterns. |
| R04 | ML I/O contention, caching, and prefetching considerations. |
| R18 | Rack/rail-aware placement and storage-network placement guidance. |
| R28 | Far-memory hierarchy and runtime resource management context. |
| R30 | Reactive/proactive LLM workload scheduling and heterogeneous accelerator contention. |
| R31, R36 | AI data-center power, energy-storage, and facility telemetry constraints that affect admission. |
| R34, R37 | OCP inference/training cluster profiles, rail topology, gateway/storage separation, lifecycle, and observability. |
| R38 | OCS as a future dynamic cluster-reconfiguration option that scheduler policy must explicitly gate. |
| R251, R252 | BMRA telemetry-aware scheduling and QAT trust/VF/PF/endpoint/fallback state used as scheduler inputs. |
| R29, O10, O11, ADR-015 | CXL memory expansion, form-factor/topology choices, and placement-governance requirements. |

## Pod-scale update: UA-Link, CXL pool, rail, and heterogeneous accelerator locality

The pod-scale update adds scheduler dimensions for UA-Link pod membership, CXL pool ownership/health, rail/NIC/GPU affinity, DPU locality, and heterogeneous accelerator profiles. Admission must prefer same-pod/same-rail placement for collective-heavy and KV-hydration-heavy scopes, demote stale fabric telemetry, and avoid mixed-vendor critical inference placements unless the collective/runtime profile is qualified.
