# Failure Semantics Matrix

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Invariants

1. vLLM and peer inference actors interact only with Coherence-CE.
2. Correctness wins over availability: wrong KV is never served.
3. Durability is class-specific and must not be implied by cache hit.
4. Missing telemetry is unknown, not healthy.
5. Ambiguous writers or ambiguous storage ownership block durable acknowledgements.
6. DPU/SmartNIC host fallback is degraded resilience, not normal production posture.
7. CXL is an explicitly qualified memory tier; hidden switch/bifurcation, stale topology, or ambiguous persistence means unknown, not healthy.
8. QAT is a trusted crypto/compression accelerator only; untrusted guest exposure, ambiguous PF/VF state, endpoint reset, or stale QAT telemetry means unknown, not healthy.

## Class behavior summary

| Class | Normal behavior | Fault behavior |
| --- | --- | --- |
| KV-D0 | Active volatile decode, request-scoped | Lose/fail/retry/recompute according to request policy |
| KV-D1 | Mesh-replicated recomputable cache | Miss/recompute; do not treat loss as durable loss |
| KV-D2 | Write-back reusable prefix | If pending, recompute allowed; if durable, hydrate after recovery |
| KV-D3 | Write-through warm prefix | Queue/throttle/fail new publishes until durable backing is safe |
| KV-D4 | Extendable session/checkpoint | Fence writer; recover to last durable epoch |
| KV-D5 | Governed/audit/compliance | Fail closed unless durability, retention, and provenance evidence are available |

## Failure mode matrix

| Failure mode | Detection source | KV-D0/KV-D1 | KV-D2 | KV-D3 | KV-D4 | KV-D5 | Scheduler state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vLLM worker crash | runtime heartbeat, request trace | Request dies or recomputes | Recompute/publish from surviving mesh state | No effect unless publish in flight | Recover session from durable epoch | No loss if durable ack existed | AMBER for affected worker |
| Coherence member loss | mesh membership, partition ownership | Use replica or recompute | Use replica, flush/replay pending queue | Serve only proven durable or replicated state | Fence/reassign writer epoch | Serve only proven retained data | AMBER/RED by replica deficit |
| Coherence quorum loss | quorum state | Recompute only where safe | Stop new write-back growth | Stop new durable publishes | Fence writers | Fail closed | RED for durable classes |
| Write-back queue worker loss | queue heartbeat, sequence gaps | Not applicable | Replay idempotent records; pending may recompute | Cannot mark durable without ack | Replay versioned records only | Replay retained records only | AMBER/RED by queue age |
| Storage-node loss | substrate health summary | Recompute if needed | Pending data recomputable; durable data hydrate from surviving owner | Queue writes until durable path safe | Fence and recover checkpoints | Fail closed if retention path unsafe | AMBER/RED |
| OpenZFS pool degraded | pool health, checksum, latency | No direct dependence | Throttle flush; recompute pending data | Queue/throttle durable writes | Checkpoint writes blocked if unsafe | Fail closed if retention/audit unsafe | AMBER/RED |
| Cross-node mirror split | fencing service, ownership epoch | No direct dependence | Stop durable promotion | Stop durable acks | Fence writers | Fail closed | RED |
| NVMe device failure | storage health summary | No direct dependence | Throttle/flush by policy | Continue only if redundancy and latency gates pass | Continue only if checkpoint SLO passes | Continue only if retention policy passes | AMBER/RED |
| DPU/SmartNIC offload failure | offload telemetry, fallback state | AMBER if runtime unaffected | AMBER; throttle durable traffic | AMBER/RED by durable p99 | RED if writer/checkpoint path affected | RED unless approved contingency | AMBER/RED/DRAIN |
| QAT endpoint/VF/PF/service fault | QAT telemetry, PF/VF map epoch, driver/firmware version, endpoint errors, reset events, trust scope | CPU fallback or AMBER if unaffected | AMBER/RED if QAT-assisted compression/crypto path affected | Queue/throttle if durable transform depends on QAT and fallback is unqualified | Fence QAT-dependent writer/checkpoint path | Fail closed if retention/audit crypto depends on QAT and fallback evidence is absent | AMBER/RED/DRAIN |
| CXL device/link/topology fault | CXL telemetry, inventory epoch, link state, ECC/media errors, thermal state | Recompute or use DRAM if CXL was only capacity relief | AMBER/RED by pending CXL role; demote to DRAM/T2 | RED for new durable writes if CXL was in durable path | Fence CXL-dependent writer/checkpoint path | Fail closed if retention/audit depends on CXL | AMBER/RED/DRAIN |
| CXL fabric-manager or pool-ownership fault | CFM/fabric-manager state, pool ownership epoch, fence state, hotness/migration telemetry | Recompute or use DRAM/local placement | Stop CXL pool growth; demote warm/pending data to DRAM/T2 | RED for CXL-dependent durable publishes | Fence CXL-dependent writers/checkpoints | Fail closed if retention/audit depends on CXL pool | RED/DRAIN |
| RoCEv2 path loss or congestion | fabric telemetry, RTT/drop/CNP/PFC | Reduce concurrency/recompute | Throttle hydration/flush | Queue durable writes if p99 unsafe | Fence/queue if writer path unsafe | Fail closed if audit path unsafe | AMBER/RED |
| Rack power/thermal event | platform telemetry | Drain or reduce concurrency | Pause background flush/promotion if needed | Queue writes if safe power not available | Checkpoint before drain if possible | Fail closed if retention cannot be maintained | AMBER/DRAIN/RED |
| Timing fault | timing validation | Ignore cross-node timing SLO evidence | Conservative lag calculations | No new durable promotion based on suspect time | Rely on epochs, not clocks | Fail closed if audit ordering unsafe | AMBER/RED |
| Metrics stale | freshness monitor | AMBER if low risk | AMBER/RED by class | RED for new durable writes | RED for writers | RED | AMBER/RED |
| Scheduler policy bug suspected | decision-log anomaly | Drain affected scope | Drain affected scope | Drain durable publishes | Fence writer admission | Fail closed | DRAIN |

## Recovery checklist

- [ ] Stop or reduce admission for affected class/scope.
- [ ] Capture decision logs and Coherence summary epoch.
- [ ] Capture Coherence membership, partition ownership, writer epochs, write-back queue heads/tails, and failed records.
- [ ] Capture storage health summary and pool/checksum/latency state from owning storage service.
- [ ] Capture DPU/offload state and fabric health summary.
- [ ] Capture QAT device model, integrated/AIC form, PF/VF assignment, trust scope, driver/firmware version, kernel/VM machine type, endpoint errors, reset state, service state, fallback state, and telemetry epoch.
- [ ] Capture CXL role, OCP CMS topology class, CPU socket/root complex, NUMA node, link width/speed, switch hop count, bifurcation state, firmware, fabric-manager/CFM state, pool ownership epoch, fence state, hotness/migration state, error/thermal state, and telemetry epoch.
- [ ] Fence ambiguous writers and storage ownership.
- [ ] Replay idempotent write-back/write-through records.
- [ ] Run class-specific canaries before GREEN admission.
- [ ] Document observed behavior against this matrix.

## Required drills

| Drill | Pass condition |
| --- | --- |
| Runtime crash during prefill | Request recomputes or fails cleanly; no wrong KV is served. |
| Coherence member loss | Ownership moves with epoch evidence; incompatible/stale KV rejected. |
| Write-back lag spike | KV-D2 moves AMBER/RED without claiming durability. |
| Durable backing unavailable | KV-D3+ publishes queue/reject; KV-D5 fails closed. |
| Storage-node split | Durable acknowledgements stop until fencing is proven. |
| DPU fallback | Admission state changes and fallback is visible. |
| QAT endpoint, VF/PF, or service fault | QAT-dependent placement moves AMBER/RED/DRAIN; CPU fallback is used only when qualified; untrusted or ambiguous VF/PF assignment is rejected. |
| CXL topology, device, or fabric-manager fault | CXL-dependent placement moves AMBER/RED/DRAIN; volatile CXL never produces durable acknowledgement; ownership/fencing plus demotion/rollback path are visible. |
| Fabric congestion | Hydration/write p99 drives throttling before TTFT/TPOT collapse. |
| Stale telemetry | Scheduler treats state as unknown and conservative. |
| Rack power/thermal event | Background work drains; durable classes preserve safety. |

## Owning ADRs

- ADR-010: write policy to OpenZFS.
- ADR-011: KV durability classes.
- ADR-013: failure semantics and fencing.
- ADR-014: scheduler rollup and admission states.
- ADR-015: CXL memory tiering, topology governance, and OpenZFS interaction.
