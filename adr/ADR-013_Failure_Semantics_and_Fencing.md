# ADR-013: Failure Semantics and Fencing

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Define failure semantics for the full Project Coherent Storage stack: inference runtimes, Coherence-CE, OpenZFS/NVMe-oF storage nodes, DPU/SmartNIC offload, RoCEv2 fabrics, rack/facility systems, timing, telemetry, and scheduler admission. The core invariant is that the system may miss, recompute, queue, drain, or fail closed, but it must never serve wrong KV or acknowledge durability it cannot prove.

## Context

The architecture intentionally separates layers. vLLM and peer runtimes are Coherence-CE clients only. Coherence-CE owns KV identity, placement, replication, hydration, write-back, write-through, replay, and scheduler-facing summaries. OpenZFS/NVMe-oF provides the durable NAND block substrate below Coherence-CE. DPUs/SmartNICs are required on storage-network paths for hardware offload and RDMA resource mediation. RoCEv2 fabric health, power/facility readiness, and timing/telemetry freshness all affect whether a path is safe to admit.

Without explicit failure semantics, operators may confuse a cache miss with data loss, DPU fallback with normal operation, a mirrored substrate split with safe durability, or stale metrics with healthy admission. This ADR makes those behaviors explicit.

## Decision

- Use durability class to select failure behavior.
- Prefer recompute/miss for KV-D0 through KV-D2 when correctness is preserved.
- Require queue, fence, or fail-closed behavior for KV-D3 through KV-D5 when durable evidence is unavailable.
- Fence all single-writer session/checkpoint state with monotonic epochs.
- Fence storage-node and OpenZFS import/failover paths so no durable dataset or namespace has concurrent ambiguous writers.
- Treat DPU/SmartNIC failure as storage-path degradation requiring telemetry, drain, or host-mediated fallback; it is not a transparent normal state.
- Treat QAT endpoint, VF/PF, driver, firmware, or service failure as accelerator-path degradation: drain or fall back to CPU/host software, and never let QAT availability imply durability, storage ownership, or safe guest trust.
- Treat missing telemetry as unsafe for promotion and conservative for admission.

## Failure invariant matrix

| Failure domain | Required behavior |
| --- | --- |
| vLLM/runtime worker crash | Coherence-CE keeps reusable KV by class; active KV-D0 dies with worker/request. New worker may lookup compatible KV or recompute. |
| Coherence-CE member loss | Partition ownership moves only with epoch/quorum evidence. KV-D0 may be lost. KV-D1/KV-D2 may recompute. KV-D3+ requires durable/replica proof before serving. |
| Coherence quorum loss | Stop new durable publishes. Serve only data whose class and policy can be proven safe by remaining quorum/local durable evidence. |
| Write-back worker loss | Replay idempotent queue records. Pending KV-D2 may revert to recompute if not durable. KV-D3+ cannot be marked durable without backing-store ack. |
| OpenZFS pool degraded | Continue reads only within class SLO and checksum/pool-health policy. Throttle/queue durable writes and mark admission AMBER/RED. |
| OpenZFS split/import ambiguity | Fence before import. No dual writer. Durable acknowledgements stop until ownership is unambiguous. |
| NVMe device failure | OpenZFS mirror/resilver policy applies below Coherence-CE. Scheduler sees degraded substrate and may drain durable writes. |
| DPU/SmartNIC failure | Drain offloaded path or switch to documented host-mediated degraded path; emit fallback state; no production-like promotion while required offload telemetry is absent. |
| QAT endpoint, VF/PF, driver, firmware, or service failure | Drain QAT-dependent crypto/compression paths or fall back to CPU software; stop QAT passthrough/VF use for affected trusted guests; do not remove host QAT drivers while guest VFs are active; mark admission AMBER/RED by affected class/path. |
| CXL device, switch, fabric-manager, or pool-ownership fault | Demote CXL-dependent warm data to DRAM/T2 where possible; fence shared-pool writes; reject new CXL-dependent durable placement; never treat volatile CXL as durability evidence. |
| RoCEv2 path failure | Use qualified A/B path failover where available. If congestion/partition affects hydration or durable writes, scheduler changes admission. |
| Rack power/thermal event | Freeze nonessential rebuild/write-back/promote work; protect durable writes by class; drain interactive admission if power/thermal headroom is unsafe. |
| Timing/clock fault | Stop using cross-node timing as evidence for ordering or latency SLOs; require monotonic service epochs and conservative admission. |
| Metrics/telemetry stale | Scheduler treats stale source as unknown, not healthy. Class-specific admission becomes AMBER/RED based on risk. |

## Class-specific failure behavior

| Class | Data loss allowed? | Recompute allowed? | Serve stale? | Durable write behavior during fault |
| --- | --- | --- | --- | --- |
| KV-D0 | Yes, request-scoped | Request/runtime policy | Never | No durable obligation |
| KV-D1 | Yes, cache-scoped | Yes | Never | No durable obligation |
| KV-D2 | Pending write-back may be lost | Yes until durable | Never | Stop growth or flush when queue/fabric/storage unsafe |
| KV-D3 | No after durable ack | No unless tenant explicitly allows demotion | Never | Queue/throttle/fail until durable ack path recovers |
| KV-D4 | No beyond last durable epoch | Resume from last durable epoch | Never | Fence writer and recover/replay by epoch |
| KV-D5 | No | No | Never | Fail closed unless durability and retention evidence are present |

## Fencing rules

- Coherence-CE assigns ownership epochs to partitions, prefix shards, and session writers.
- Every KV-D4 writer must hold a valid single-writer epoch before appending or checkpointing.
- Write-back records include idempotency key, sequence, class, identity hash, payload hash, and target manifest epoch.
- OpenZFS-backed durable services must be imported or mounted read-write only by the fenced owner for that namespace/dataset role.
- A fabric partition that prevents fencing evidence from propagating blocks new durable acknowledgements.
- Recovery code must prefer duplicate-safe replay over best-effort repair.

## Recovery order

1. Stop admission for affected classes and scopes.
2. Preserve evidence: Coherence membership, ownership epochs, write-back queue heads/tails, OpenZFS pool status, DPU/fabric state, QAT device/VF/PF/driver/firmware/service state, CXL role/topology/fabric-manager/pool-ownership state, and scheduler decisions.
3. Fence ambiguous writers and storage paths.
4. Restore Coherence partition ownership or mark affected partitions unavailable.
5. Recover OpenZFS pools/namespaces only after ownership is unambiguous.
6. Replay idempotent write-back/write-through records.
7. Run class-specific canaries: miss/recompute for KV-D0 through KV-D2, durable hydrate for KV-D3, epoch resume for KV-D4, retention/audit verify for KV-D5.
8. Move admission from RED to AMBER to GREEN only after telemetry freshness and SLO gates pass.

## Positive consequences

- Failure drills can be written as executable expectations instead of subjective outcomes.
- Cache loss, durable loss, and unavailable durability are distinguishable.
- DPU/fabric/storage degradation becomes visible to the scheduler without leaking details to vLLM.
- Split-brain and stale-KV hazards are handled by explicit fencing and version rejection.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Conservative failure policy reduces availability | Let lower durability classes recompute while durable/governed classes queue or fail closed. |
| Fencing implementation is incomplete | Gate production-like KV-D4/KV-D5 on explicit partition, storage import, and writer-epoch drills. |
| DPU fallback masks offload failure | Mark fallback as degraded, report it to scheduler, and require remediation before GREEN admission. |
| QAT endpoint failure or malformed request affects other tenants | Restrict QAT to trusted guests/users, use device/file permissions, keep CPU fallback, and drain/fence affected accelerator scopes after endpoint or VF/PF anomalies. |
| Telemetry gaps hide failures | Missing required telemetry maps to AMBER/RED depending on class and path. |
| Recompute storms after failure | Rate-limit recompute, protect hot prefixes, and admit based on recompute budget. |

## Acceptance criteria

- Failure drills exist for runtime crash, Coherence member loss, quorum loss, write-back replay, OpenZFS degradation, storage-node fencing, DPU fallback, QAT endpoint/VF/PF/driver/service fault, CXL device/topology/fabric-manager/pool-ownership fault, RoCEv2 path loss, telemetry staleness, and rack power constraints.
- Each drill has expected behavior by KV-D0 through KV-D5.
- Split/import ambiguity blocks durable acknowledgements.
- DPU fallback changes admission state and is visible in scheduler decision logs.
- Stale metrics are treated as unknown/unhealthy for class-dependent admission.
- No failure drill produces wrong-version or incompatible KV service.

## Source documents

| ID | Use |
| --- | --- |
| A0, A1, A2 | Baseline rack, storage, DPU, fabric, and coherent NAND requirements. |
| R01, R02, R03 | Inference runtime, scheduling, and KV correctness pressures. |
| R05, R06, R07, R08, R09, R15 | DPU/RDMA offload, resource isolation, and protocol trade-offs. |
| R10, R11, R12, R13, R14, R19, R20 | RoCEv2 congestion, multipath, traffic-class, and telemetry failure modes. |
| R31, R32, R33, R34, R35, R36, R37, R40, R41, R42 | Power, timing, management, and OCP fabric/facility constraints. |
| O01, O02 | Coherence write/retry/persistence semantics. |
| O04, O06, O07 | OpenZFS sync, scrub/resilver, and scheduler behavior. |
| O14-O29, ADR-015 | CXL device, switch-fabric, fabric-management, hotness, pool-ownership, and topology failure semantics. |
| R251, R252 | BMRA deployment/verification and QAT trust, Xen/SR-IOV, endpoint, VF/PF, reset, driver, and virtualization failure semantics. |
