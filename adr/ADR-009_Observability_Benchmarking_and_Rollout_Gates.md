# ADR-009: Observability, Benchmarking, and Rollout Gates

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Architecture diagram

![ADR-009_Observability_Benchmarking_and_Rollout_Gates](diagrams/ADR-009_Observability_Benchmarking_and_Rollout_Gates.png)

## Decision summary

Gate Project Coherent Storage 2026-Q2 rollout on LLM-visible performance, storage/fabric telemetry, failure drills, reproducibility, and rollback evidence. Link speed, raw IOPS, and one-off benchmark throughput are not sufficient for production-like promotion.

## Context

The baseline ADR set defined fabric, storage, automation, and observability gates. The inference-optimized architecture adds additional failure modes: KV cache fragmentation, prefix-cache misses, cold model loads, vector-index tail latency, RAG recall regressions, DPU offload opacity, GPU-direct security boundaries, and background jobs competing with interactive decode.

The RAG corpus reinforces that inference quality depends on end-to-end behavior: scheduling, batching, memory management, storage paths, network congestion, and retrieval all contribute to user-visible latency. The 2026 OCP additions make power/facility telemetry, time synchronization, OCP cluster lifecycle state, management-channel health, MRC/OCS canary behavior, and extraction coverage part of the rollout evidence set.

The Intel BMRA/QAT post-refresh sources add two rollout requirements. First, lab deployment must be reproducible from profile-driven automation: BIOS, kernel boot parameters, IOMMU/SR-IOV, hugepages, device plugins, telemetry-aware scheduling, and post-deployment checks must be captured as artifacts. Second, QAT acceleration must be tested as a faultable local accelerator with explicit trust, reset, VF/PF, and fallback semantics rather than as a transparent CPU feature.

## Decision

- Define rollout gates around TTFT, TPOT, end-to-end latency, cache-hit rate, model-load latency, vector-search latency, retrieval quality, and storage/fabric health.
- Require benchmark scenarios that exercise both hot-hit and cold-miss paths.
- Require failure drills for fabric, storage node, DPU, index shard, model replica, and cache-node failures.
- Record test inputs, model versions, corpus versions, hardware inventory, firmware, runtime versions, fabric configuration, and storage layout for each benchmark run.
- Treat any missing DPU, fabric, storage, or inference telemetry as a rollout blocker for that path.
- Keep every optimization reversible through host-mediated fallback, previous manifest, or traffic drain.
- Gate multi-rack rollout on rack/facility power state, PSU/power-shelf health, ESS/backup posture, timing validation, management-channel reachability, source-corpus extraction coverage, and CXL topology/telemetry qualification when those signals affect the path under test.
- Gate lab-profile promotion on BMRA-style reproducibility evidence: inventory, BIOS/UEFI, kernel boot parameters, IOMMU/SR-IOV, hugepages, device-plugin state, telemetry stack health, and Ansible/playbook version.
- Gate QAT-enabled paths on device/driver/firmware version, PF/VF mapping, trusted guest or driver-domain assignment, q35/VM compatibility where passthrough is used, endpoint health, reset/quiesce drills, and CPU fallback.

## Required metric families

| Family | Metrics |
| --- | --- |
| LLM request | TTFT, TPOT, total latency, request queue time, decode queue time, tokens/sec, error rate |
| Coherence-CE KV/prefix | Prefix hit rate, mesh API latency, KV block allocation failures, hydration latency, evictions, recompute count, wrong-version rejects, backing-tier operation state |
| Model/object | Model-load p50/p95/p99, warmup time, object read throughput, shard fanout, manifest version |
| RAG/vector | Embedding latency, vector-search latency, chunk-hydration latency, recall sample result, retrieval cache hit rate |
| Accelerator | GPU utilization, HBM free/used, KV memory use, preemption, OOM, copy-engine utilization |
| Host memory | DRAM pressure, pinned memory, hugepages, allocator fragmentation, page faults |
| Host/QAT acceleration | QAT device state, driver/firmware version, PF/VF mapping, SR-IOV trust state, service profile, crypto/compression request errors, endpoint reset state, utilization/rate-limit state, fallback state, telemetry freshness |
| CXL tier/topology | CXL capacity/pressure, p50/p95/p99 access latency, bandwidth, NUMA distance, CPU socket/root complex, link width/speed, switch hop count, bifurcation state, ECC/media errors, thermal/throttle state, firmware, telemetry freshness |
| ZFS/NVMe | Pool health, vdev latency, ARC hit rate, zvol latency, NVMe queue depth, media writes, scrub/resilver state |
| RDMA/fabric | ECN, CNP, PFC pause, drops, retransmits/timeouts, RTT, link utilization, path asymmetry |
| DPU/SmartNIC | CPU, memory, queue depth, drops, offload service health, firmware, fallback state |
| Scheduler | Admissions, rejections, reroutes, warmups, evictions, preemptions, degradation decisions |
| Facility/power | Rack power headroom, PSU/power-shelf health, ESS/backup readiness, power quality, thermal state, power-event correlation |
| Timing/management | Clock error state, boundary/transparent clock health, holdover test state, DC-SCM/OBMF/BMC management-channel health |
| Corpus/extraction | Source count, extraction coverage, failed extraction list, source-ID manifest version, impact-ledger version |

## Benchmark matrix

| Scenario | Purpose |
| --- | --- |
| Coherence-CE hot prefix hit | Validate best-case KV reuse and low TTFT through the mesh API. |
| Coherence-CE cold prefix miss | Validate recompute, mesh hydration, and backing-tier tail behavior without client storage coupling. |
| Cold model load | Validate model/object tier and admission policy. |
| Warm model plus remote Coherence-CE KV | Validate cross-rack mesh hydration policy. |
| RAG hot index | Validate vector lookup and chunk hydration under normal interactive load. |
| RAG cold shard | Validate index/corpus cache miss behavior. |
| Batch plus interactive | Validate background work cannot starve interactive inference. |
| Fabric congestion | Validate traffic classes, ECN/PFC response, and scheduler throttling. |
| DPU fallback | Validate host-mediated fallback and telemetry continuity. |
| QAT crypto/compression canary | Validate QAT device discovery, trusted VF/PF assignment, crypto/compression correctness, decompression buffer guards, endpoint-hang handling, reset/quiesce behavior, CPU fallback, and scheduler reason codes. |
| CXL tier canary | Validate DRAM versus CXL warm-tier behavior, same-root-complex placement, hidden switch/bifurcation rejection, explicit CXL switch-fabric qualification, and scheduler class limits. |
| ZFS scrub/resilver | Validate durability work under inference load. |
| Node/fabric failure | Validate failover without corrupting manifests or cache identity. |
| Timing validation | Validate boundary/transparent clock, transient, noise, and holdover behavior before using timing data for multi-rack evidence. |
| Power-constrained storage maintenance | Validate scrubs, resilvers, cache warmup, and model/index rebuilds against rack power, PSU, ESS, and thermal telemetry. |
| MRC/OCS candidate | Validate transport or optical reconfiguration against latency, jitter, retransmission/reconfiguration, observability, and rollback gates before promotion. |
| Corpus refresh | Validate extraction coverage and source-impact ledger before RAG-derived ADR or index promotion. |

## Rollout stages

| Stage | Promotion gate |
| --- | --- |
| Lab baseline | Hardware inventory, firmware, BIOS/UEFI, kernel boot parameters, IOMMU/SR-IOV, hugepages, fabric QoS, pool layout, QAT role inventory where present, CXL role/topology inventory, rack/facility power, timing profile, management path, corpus manifest, and telemetry are recorded. |
| Single-node canary | Model load, local Coherence-CE KV, local RAG, and fallback paths meet p50/p99 gates. |
| Single-rack canary | Rack-local model, Coherence-CE KV, RAG, and fabric traffic-class gates pass. |
| Dual-fabric canary | Fabric A/B failover and path asymmetry drills pass. |
| Multi-rack pilot | Scheduler locality, replica placement, cache hit rate, and congestion gates pass. |
| Production-like service | Failure drills, rollback, recall-quality, security, and observability gates pass. |

## Rollback policy

- Every promoted manifest must retain the previous manifest until rollback has been tested.
- DPU-assisted paths must be drainable back to host-mediated paths.
- GPU-direct paths must be disableable without changing object identity.
- Quantized KV or vector-index variants must be demotable to unquantized or prior versions.
- Model, corpus, embedding, and index aliases must be atomically reversible.
- Scheduler policy changes must be versioned and revertible.
- CXL tier enablement must be reversible by class/profile: demote to DRAM/T2, drain warm-tier use, or disable CXL admission without changing vLLM API behavior.

## Positive consequences

- Storage architecture decisions are judged by inference outcomes.
- Rollout can stop at the failing layer with enough telemetry to explain why.
- Optimizations such as DPU offload, GPU-direct, multipath, and quantization can be introduced without losing rollback safety.
- RAG quality is protected alongside latency.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Benchmark suite becomes too large to run often | Split into fast canary, nightly, and release-gate profiles. |
| Metrics exist but are not tied to requests | Require request IDs to propagate through scheduler, model, Coherence-CE KV, RAG, storage, and fabric logs with layer ownership preserved. |
| Synthetic tests miss production behavior | Capture production-like traces and replay sanitized request mixes. |
| Rollback is untested until an outage | Include rollback drills in every rollout stage. |
| Facility or timing telemetry is missing | Treat missing rack power, PSU, ESS, timing, or management-channel telemetry as a rollout blocker for dependent paths. |
| RAG-derived decisions are not reproducible | Require extraction report, source manifest, and impact ledger before promoting ADR or index updates. |
| CXL qualification misses physical topology | Require source-of-truth inventory and canaries for socket/root complex, switch hop count, bifurcation, link width/speed, thermal state, and p99 latency. |
| QAT acceleration hides reset, guest trust, or endpoint-fault risk | Treat QAT as a qualified accelerator path with trusted-guest policy, CPU fallback, endpoint-reset drills, host-driver-removal prohibition while guests are active, and telemetry reason codes. |
| Lab automation drifts from host BIOS/kernel state | Persist BMRA-style preflight artifacts: inventory, BIOS/UEFI, kernel command line, IOMMU/SR-IOV, hugepages, device plugins, telemetry stack, playbook versions, and post-deployment verification output. |

## Acceptance criteria

- A benchmark report includes exact model, corpus, embedding, index, runtime, firmware, fabric, DPU, storage, and scheduler policy versions.
- The fast canary profile measures TTFT, TPOT, Coherence-CE KV hit/miss, model load, vector search, chunk hydration, RDMA health, and ZFS health.
- A failed rollout gate produces a clear blocker with owning subsystem and rollback recommendation.
- Request-level traces join scheduler, inference runtime, Coherence-CE KV, RAG, storage, DPU, and fabric events without exposing storage-layer control to runtime clients.
- A rollback drill succeeds for model manifest, vector-index manifest, DPU offload, GPU-direct, and scheduler policy changes.
- No new data path is promoted if telemetry is missing for its failure mode.
- Multi-rack canary evidence includes rack power, PSU/power-shelf, ESS/backup, timing, and management-channel health where applicable.
- ADR or RAG-index promotion includes a source manifest, extraction report, failed-source list, and source-impact ledger.
- CXL promotion evidence includes CXL-vs-DRAM latency, topology inventory, telemetry freshness, thermal/error state, switch/bifurcation qualification, and rollback/demotion evidence.
- QAT promotion evidence includes crypto/compression correctness, QAT endpoint/VF/PF health, trusted-assignment proof, reset/quiesce behavior, CPU fallback, rate-limit/utilization telemetry when supported, and scheduler reason-code coverage.
- Lab deployment evidence includes BMRA-style Ansible/profile reproducibility plus post-deployment checks for Kubernetes/VM/device-plugin/telemetry components when those layers participate in the test.

## Source documents

| ID | Use |
| --- | --- |
| A0 | Existing observability, security, automation, and SLO governance baseline. |
| R01, R02 | LLM memory/scheduling metrics and inference runtime pressure points. |
| R03 | TTFT, TPOT, HPC serving metrics, and RAG serving context. |
| R04 | ML I/O contention and cache/prefetch behavior to benchmark. |
| R10, R11, R12, R13, R14 | Fabric congestion, RoCE scaling, multipath, and path-selection behavior. |
| R16, R17 | GPU-direct and GPU-initiated networking paths to benchmark and gate. |
| R18, R19, R20 | Validated AI fabric design and operational telemetry requirements. |
| R22, R23, R24 | ZFS and media-layout behavior to monitor under load. |
| R25, R26, R27 | Quantized KV/vector alternatives requiring quality and rollback gates. |
| R31, R35, R36, R41, R42 | Power, ESS, HVDC/LVDC, power-quality, and AI data-center telemetry gates. |
| R32, R33, R40 | Timing and management-channel validation gates. |
| R34, R37 | OCP inference/training fabric lifecycle, observability, and cluster profile validation. |
| R38, R39 | OCS and MRC candidate-path gates for latency, jitter, reliability, congestion, and rollback. |
| R43 | Failed extraction accounting; retained as reference-only evidence and not used for decision promotion. |
| R28, R29, O10, O11, O12, O13, ADR-015 | CXL/PMem observability, topology, and rollout-gate requirements. |
| R251 | BMRA automation, BIOS/kernel/SR-IOV/hugepage/device-plugin, telemetry-aware scheduling, and post-deployment verification evidence. |
| R252 | QAT feature/limitation, Xen/SR-IOV/VF/PF, endpoint, reset, trust, and compression/crypto failure evidence. |
