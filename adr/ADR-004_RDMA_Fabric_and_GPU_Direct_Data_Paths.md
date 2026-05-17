# ADR-004: RDMA Fabric and GPU-Direct Data Paths

**Project:** Project Coherent Storage  
**Version:** 2026-Q2  
**Package:** v2 inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Treat the RoCEv2 fabric as an inference data plane with isolated traffic classes, rack/rail locality, adaptive multipath, receiver-aware admission, and GPU-direct capable storage reads where the hardware and runtime are qualified.

## Context

The v0 fabric decision established dual independent lossless RoCEv2 fabrics with PFC, ECN/DCQCN, jumbo MTU, and telemetry gates. The research corpus shows that large AI fabrics require more than enabling RoCE. PFC can create head-of-line blocking, DCQCN is workload-sensitive, ECMP can underuse path diversity, AI workloads create elephant flows and incast-like bursts, and GPU-directed or GPU-initiated communication is increasingly important.

Inference storage has multiple traffic shapes that should not all share one priority: Coherence-CE mesh/client API calls, Coherence-CE mesh-to-storage hydration/persistence, large model loads, vector index reads, corpus chunk reads, checkpoints, logs, and control-plane operations. The 2026 OCP inference and training fabric RAs add concrete cluster profiles, SONiC lifecycle expectations, rail-optimized topology, RoCE-oriented QoS, and Day-2 observability. OCP MRC also introduces a candidate multipath reliable transport model, while OCS is a future fabric option for lower power, jitter, and reconfiguration rather than a default data path.

## Decision

- Preserve v0 Fabric A/B physical independence and RDMA validation gates.
- Add inference traffic classes and admission policies for KV hydration, model/object loads, RAG/vector reads, checkpoint/artifact I/O, accelerator collectives, and control traffic.
- Use PFC only on approved lossless RDMA priorities. Do not make the whole fabric lossless.
- Use ECN/CNP telemetry and switch/NIC counters as rollout gates, but do not assume DCQCN tuning alone will solve all AI traffic patterns.
- Prefer rail-aware and rack-local placement for accelerator hosts and storage/cache nodes. The scheduler must understand rack, rail, fabric plane, and congestion state.
- Qualify GPU-direct storage and GPU-direct RDMA paths per platform. If unsupported, use pinned host memory and DPU/host copy paths with explicit SLO accounting.
- Use adaptive multipath where available and qualified. Host-based path switching or software multipath RDMA may be used before switch/NIC transport changes.
- Treat MRC-style packet spraying, path-aware event selection, and SACK/NACK reliability as a qualified future transport profile, not as a silent replacement for the current RoCEv2 baseline.
- Treat OCS as a future or special-purpose fabric reconfiguration option that must prove latency, jitter, power, operational, and failure-domain behavior before carrying inference storage traffic.
- Include clock/timing validation and management-plane modularity in multi-rack rollout gates when timing is used for request tracing, ordering diagnostics, congestion analysis, or fabric correlation.

## Traffic classes

| Class | Examples | Fabric policy |
| --- | --- | --- |
| Coherence-CE client API | vLLM/peer runtime calls to Coherence-CE for prefix/KV data | Inference service priority; no direct storage, DPU, NVMe-oF, RoCEv2, or RDMA exposure to clients |
| Coherence-CE mesh/storage path | Mesh replication, hydration, persistence, rebuild, backing-store I/O | Highest storage-side KV priority, bounded payloads, admission-gated |
| Model/object load | Weight shard prefetch, runtime artifact load | High throughput, rate-limited, separate from KV hot path |
| RAG/vector | Vector index probes, corpus chunk reads | Low tail latency, can use replicated local shards |
| Checkpoint/artifact | Batch outputs, checkpoints, logs | Throughput class, never blocks interactive KV |
| Accelerator collective | GP-GPU/NPU collectives and scale-out traffic | Workload-specific rail and traffic profile |
| Control/observability | NetBox, Ansible, telemetry, logs | Reliable control VRF, not lossless RDMA |
| Timing/management | PTP timing, boundary-clock telemetry, DC-SCM/OBMF management | Reliable management/control path; validates correlation and platform health rather than carrying hot data |

## GPU-direct policy

- GPU-direct reads are allowed only when NIC, GPU, PCIe topology, driver, runtime, and security posture are recorded in source-of-truth.
- GPU-direct access must be benchmarked against host-pinned and DPU-assisted paths for p50/p99 latency, throughput, CPU load, and failure behavior.
- The storage service must never grant broad remote memory access to untrusted tenants. GPU-direct capabilities are mediated by trusted runtime, DPU, or storage gateway policy.
- Direct paths are an optimization, not the only correctness path. Every production canary namespace must have a host-mediated fallback.

## Multipath and congestion policy

- Use multiple queue pairs and multiple fabric endpoints for high-throughput flows.
- Avoid single-flow assumptions for large RDMA transfers. Split model/object transfers into schedulable chunks where supported.
- Monitor path RTT, ECN marks, CNP, PFC, queue depth, retransmission/timeouts, and fabric asymmetry.
- If adaptive routing, packet spraying, or alternative transport is introduced, it must pass out-of-order, retransmission, and tail-latency gates before general use.
- Receiver-driven or application-level admission may be used to limit inflight KV/model transfers during congestion.
- MRC, packet spraying, adaptive routing, and OCS are disabled for production-like inference storage until conformance, retransmission, out-of-order, jitter, and rollback gates pass.

## Positive consequences

- Coherence-CE client API and mesh/storage traffic are protected from large model loads and batch artifacts without exposing lower-layer fabric controls to runtime clients.
- Fabric behavior becomes part of inference placement instead of a passive network assumption.
- GPU-direct can improve high-end paths while preserving fallback and tenant safety.
- The architecture can evolve toward newer Ethernet transports without rewriting storage APIs.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Too many traffic classes become hard to operate | Start with the six classes above and require evidence before adding more. |
| PFC or ECN misconfiguration causes hidden tail latency | Enforce end-to-end QoS audits, telemetry, and controlled congestion tests. |
| GPU-direct path creates security exposure | Restrict to trusted runtimes and DPU/gateway mediated capabilities. |
| Multipath introduces out-of-order overhead | Gate with NIC support, workload tests, and p99/p999 latency thresholds. |
| New transport or optical switching option hides failure semantics | Keep RoCEv2 A/B as baseline and require explicit MRC/OCS canaries, rollback, and observability before promotion. |
| Timing telemetry is inaccurate during congestion analysis | Validate time receivers, boundary clocks, transparent clocks, transient behavior, and holdover before using timing data as rollout evidence. |

## Acceptance criteria

- A canary inference workload runs with separate Coherence-CE client, Coherence-CE mesh/storage, and model-load traffic classes, and telemetry confirms no sustained RDMA-priority drops.
- A model-load stress test cannot starve Coherence-CE KV hydration beyond the configured SLO.
- Fabric A or B failure causes controlled path failover without corrupting KV or model objects.
- At least one GPU-direct capable path is benchmarked against host-pinned fallback, or explicitly marked unsupported for the hardware profile.
- Scheduler placement records include rack, rail, fabric plane, OCP cluster profile, congestion state, and timing/telemetry freshness.
- Any MRC or OCS candidate path has a canary report covering p99/p999 latency, retransmission or reconfiguration behavior, rollback, and impact on KV/model/RAG classes.

## Source documents

| ID | Use |
| --- | --- |
| A0 | Existing dual RoCEv2 fabric baseline and telemetry gates. |
| R10, R11 | RoCE limitations, DCQCN/PFC trade-offs, AI-scale operational experience. |
| R12, R13, R14 | Multipath, adaptive load balancing, and host/software RDMA path diversity. |
| R16, R17 | GPU-direct storage and GPU-initiated networking direction. |
| R18, R19, R20 | AI fabric design, traffic classes, rail/rack locality, PFC/ECN/MTU guidance. |
| R32, R33 | Timing validation and platform management modularity for multi-rack fabric observability. |
| R34, R37 | OCP inference and training fabric RAs: profiles, rail optimization, RoCE QoS, SONiC lifecycle, and observability. |
| R38, R39 | OCS and MRC as future transport/reconfiguration candidates requiring explicit canary gates. |

## v3 research update: adjacent accelerator-storage ecosystems

The v3 evidence set retains NVIDIA BlueField/STX, Xsight/Hammerspace, Broadcom CXL/PCIe retimer, Marvell NVMe-oF, and Pure/Marvell NVMe-oF/RoCE materials. These sources are useful for fabric, DPU, signal-integrity, and AI-storage roadmap analysis. They must not be promoted to direct Marvell/XConn+CXL integration claims unless a source explicitly states that relationship.

Acceptance addition: architecture reports must classify each vendor or standard reference as direct, adjacent, negative-control, or not-found-in-current-sweep before using it as a public claim.

## v4 update: pod-scale RoCEv2 tuning and traffic-plane separation

v4 refines the RDMA fabric decision by separating UA-Link scale-up, RoCEv2/RDMA scale-out, DPU-mediated storage/NVMe-oF, management, frontend, and timing planes. RoCEv2 is accepted only with explicit traffic classes, PFC scope, ECN/DCQCN thresholds, MTU/headroom verification, rail-aware placement, stale-telemetry demotion, and rollback profiles. OCP MRC and packet-spraying techniques are tracked as future multipath/RDMA options and must be locally qualified before production use.
