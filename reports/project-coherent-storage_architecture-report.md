# Project Coherent Storage: Architecture Report

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Generated:** 2026-05-17  
**Status:** Proposed

## Executive summary

The architecture makes Project Coherent Storage pod-aware. UA-Link provides a candidate open scale-up accelerator fabric inside a pod/rack boundary; CXL memory pools provide governed warm memory capacity; RoCEv2/RDMA Ethernet remains the scale-out and storage-network data plane; DPUs/SmartNICs remain required for NVMe-oF/RDMA storage offload; and heterogeneous GP-GPU compute is admitted through scheduler capability profiles rather than vendor-specific assumptions.

The central invariant remains unchanged: vLLM and peer inference actors bind to Coherence-CE only. Coherence-CE and the scheduler decide whether state lives in GPU HBM, host DRAM, CXL memory pools, RDMA object paths, or OpenZFS-backed durable storage.

## Architecture layers

| Layer | Architecture role | Actor visibility |
| --- | --- | --- |
| Inference API | OpenAI-compatible / Coherence-native calls | Visible |
| Coherence-CE Memory Mesh | KV/prefix/object translation, durability class, placement, metrics | Visible as API semantics only |
| Accelerator scale-up | UA-Link/NVLink/vendor-local fabrics inside pod or node | Hidden |
| Warm memory tier | Host DRAM + CXL Type-3/pool T1/T1.5 | Hidden |
| Scale-out compute fabric | RoCEv2/RDMA Ethernet, rail-optimized or single-homed Clos | Hidden |
| Storage fabric | DPU-mediated NVMe-oF/RDMA to OpenZFS mirrored NAND | Hidden |
| Management/timing | BMC/Redfish/OpenBMC, PTP/timing, telemetry | Hidden |

## UA-Link pod posture

The UA-Link corpus supports an open scale-up interconnect for high-bandwidth, low-latency accelerator communication within a pod. The architecture uses UA-Link as a pod-scale accelerator-domain option, not as a replacement for Ethernet/RDMA scale-out or DPU-mediated storage. UA-Link scale-up domains should terminate at well-defined pod boundaries; cross-pod and storage traffic remains on governed Ethernet/RDMA fabrics.

Design implications:

- Keep UA-Link traffic off the storage/NVMe-oF fabric.
- Treat UA-Link pod membership as a scheduler-locality dimension.
- Expose UA-Link health, link state, switch state, and accelerator reachability to Coherence-CE admission rollups.
- Do not depend on UA-Link for durable storage semantics.
- Keep CXL memory-pool ownership separate from UA-Link accelerator-message transport, even where both live inside the same pod.

## RDMA/RoCEv2 tuning posture

The OCP inference/training fabric and lossless Ethernet corpus supports explicit RoCEv2 tuning rather than a generic “turn on RDMA” posture. The architecture requires:

- traffic classes for inference control, KV hydration, collective traffic, storage/NVMe-oF, management, and background rebuild/scrub traffic;
- PFC only on classes that require lossless behavior;
- ECN/DCQCN thresholds validated by link speed, buffer depth, and workload class;
- jumbo MTU consistency across hosts, DPUs, switches, and VLAN/VRF boundaries;
- rail-aware placement for accelerator/NIC affinity;
- dual-plane or rail-optimized topology where failure domains or bisection bandwidth require it;
- telemetry gates for pause duration, ECN marks, CNP rate, retransmits, queue occupancy, packet trimming/drops, RTT, and p99 tail latency;
- admission demotion when congestion or fabric telemetry is stale.

## CXL pool posture

CXL memory pools are admitted as T1/T1.5 warm capacity behind Coherence-CE. They are appropriate for warm KV/prefix staging, model/object metadata, vector-index heads, memory-pressure relief, and selected research paths such as CXL-KV and CXL-GPU. They are not primary KV-D0 active decode memory and do not provide durability unless the device semantics prove persistence, power-loss behavior, flush/fencing, and recovery.

CXL placement rules remain strict:

- prefer direct root-complex/NUMA locality;
- reject hidden switch/bifurcation paths for production latency roles;
- permit explicit CXL switch fabrics only with fabric-manager state, pool ownership epoch, RAS counters, p99 latency, bandwidth, failover, and rollback evidence;
- expose pool pressure and health to scheduler admission.

## Heterogeneous GP-GPU compute posture

The architecture treats NVIDIA, AMD, Intel, DPU/IPU, FPGA/NPU, and edge accelerators as capability profiles. A GPU is not “eligible” merely because it is present. Admission depends on:

- precision support and compiler/runtime stack;
- HBM capacity, bandwidth, memory pressure, and NUMA locality;
- collective library path: NCCL, RCCL, oneCCL, UCC/UCX, or cross-vendor bridge;
- RDMA direct-memory registration support such as GPUDirect or AMD DirectGMA class capability;
- UA-Link/NVLink/vendor fabric topology and scale-up domain;
- DPU/IPU proximity and storage-fabric offload path;
- CXL pool reachability and topology penalties;
- power/cooling headroom;
- live scheduler metrics and failure-domain isolation.

## Source-grounded conclusions

1. UA-Link should be modeled as a pod-scale scale-up domain, not a replacement for RoCEv2 scale-out or storage fabrics.
2. OCP OPG/XOC language is a useful scale model for 64 to 1,024 xPU pod/cluster composition.
3. RDMA/RoCEv2 tuning must be treated as an architecture surface with traffic classes, QoS, telemetry, and rollback gates.
4. CXL memory pools are increasingly relevant to KV/cache pressure, but remain Coherence-owned T1/T1.5 capacity until local hot-path evidence passes.
5. Heterogeneous GPU compute is viable only if scheduler profiles understand vendor collectives, RDMA memory semantics, and topology penalties.
6. arXiv S3 bulk archival is now supported by local scripts, pending requester-pays credentials.

## Residual risks

| Risk | Mitigation |
| --- | --- |
| UA-Link hype is mistaken for qualified production fabric | Require local link, switch, failure, latency, and scheduler drills. |
| CXL pool shared ownership is stale | Use pool ownership epochs and fence on stale fabric-manager state. |
| RoCEv2 PFC creates head-of-line blocking | Scope PFC to required classes and track pause/CNP/queue telemetry. |
| Heterogeneous GPUs create stragglers | Admit by capability profile, not nominal FLOPS. |
| Storage traffic contends with collectives | Separate traffic classes, rails, or planes; enforce admission demotion under congestion. |
| Full arXiv mirror grows without index discipline | Keep raw tar, exploded files, SQLite state, text extraction, and RAG ingest manifests separate. |

## Key sources

See `review-artifacts/rag-extraction-and-source-map.md` for full key-source mapping. Core IDs: S01 through S21.
