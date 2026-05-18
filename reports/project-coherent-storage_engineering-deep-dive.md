# Project Coherent Storage: Engineering Deep-Dive

**Project:** Project Coherent Storage
**Architecture cycle:** 2026-Q2
**Generated:** 2026-05-18
**Status:** Proposed engineering deep-dive

## Purpose

This document traverses Project Coherent Storage from the external OpenAI-compatible layer down to intra-datacenter storage mechanics. It is intended to be the top-down engineering guide that links user/API behavior, load-balancer hierarchy, Coherence-CE mesh semantics, namespace modality, scheduler admission, accelerator memory, RDMA/RoCEv2, DPU offload, and OpenZFS durable NAND.

![Top-down Project Coherent Storage stack](../diagrams/project-coherent-storage_engineering-deep-dive-stack.png)

PlantUML source: [`../diagrams/project-coherent-storage_engineering-deep-dive-stack.puml`](../diagrams/project-coherent-storage_engineering-deep-dive-stack.puml)

## Layer 1: OpenAI / User Layer

The external user layer speaks OpenAI-compatible APIs such as `/v1/chat/completions` and `/v1/responses` over HTTPS 443. Requesters may provide tenant, project, session, trace, idempotency, and Coherence policy hints, but those hints are logical. They do not select OpenZFS pools, DPUs, RDMA paths, CXL devices, VLANs, or storage nodes.

Engineering requirements:

- preserve standard OpenAI-compatible response and streaming behavior;
- whitelist only logical Coherence metadata;
- reject lower-layer selector terms in user metadata;
- propagate trace IDs and idempotency keys to Coherence-CE; and
- classify client-visible errors as retryable, throttled, recompute, incompatible, or fatal.

## Layer 2: Global Load-Balancer Mesh Pools

The global load-balancer mesh selects the best region or global service pool using tenant policy, availability, data residency, cost, service health, and request locality. It is a control and ingress layer, not a storage layer.

Engineering requirements:

- maintain global health states per region and service pool;
- avoid routing to regions whose Coherence namespace authority is RED or DRAIN for the requested tenant/model;
- preserve TLS, authentication, rate limits, and abuse controls; and
- feed global route decisions into trace context for post-incident replay.

## Layer 3: Regional Load-Balancer Mesh Pools

The regional mesh chooses a datacenter or regional Coherence ingress pool. Regional policy must consider data residency, region-local model residency, namespace authority, and cross-region cache-latency budget.

Engineering requirements:

- prefer datacenters with warm model and prefix/KV locality;
- route Dimensional Indexed Namespace requests to the declared region/datacenter authority when possible;
- avoid cross-region cache lookup unless the request allows escalation; and
- respect disaster-recovery and tenant isolation policy.

## Layer 4: Datacenter Load-Balancer Mesh Pools

The datacenter load-balancer mesh selects pod, rack, service VIP, or Coherence-CE entrypoint. This layer is where rack/pod drain, fabric health, and accelerator pool health become relevant.

Engineering requirements:

- maintain L4/L7 service pools for Coherence-CE, OpenAI-compatible gateways, translator services, and metrics endpoints;
- respect pod/rack drain states from scheduler admission;
- keep frontend/API VLANs separated from RDMA, storage, telemetry, management, and timing planes; and
- provide health checks that distinguish service process health from backend durability health.

## Layer 5: Coherence-CE Mesh Overlay

Coherence-CE is the actor-visible memory mesh and policy boundary. It owns KV/prefix-cache identity, namespace modality, durability classes, placement, hydration, write-back/write-through, metrics rollup, and API translation.

Engineering requirements:

- expose `/v1/coherence/kv/*` to vLLM adapters and OpenAI-compatible gateways;
- expose S3/Object REST translation only as a Coherence-CE API;
- support Unified Namespace and Dimensional Indexed Namespace semantics from ADR-023;
- exact prefix-cache put/get/delete must require `prefix_id`;
- search and invalidate must be explicit collection operations;
- return opaque payload references rather than physical handles; and
- feed scheduler admission with namespace, durability, fabric, CXL, DPU, and storage health summaries.

## Layer 6: Scheduler Admission and Locality

The scheduler places work based on model residency, KV/prefix locality, accelerator capacity, CXL warm-tier pressure, RDMA rail health, DPU offload health, OpenZFS durability state, tenant policy, and request SLO.

Admission states:

| State | Meaning | Typical action |
| --- | --- | --- |
| GREEN | Telemetry fresh and budget fits. | Admit. |
| AMBER | Budget may fit with controls. | Queue, prewarm, throttle, lower batch, prefer local. |
| RED | Unsafe or too slow. | Reject, recompute elsewhere, or reroute. |
| DRAIN | Existing work may complete; no new placement. | Drain pod/rack/index/namespace authority. |

Metrics must roll up by tenant, model, durability class, namespace mode, index ID, locality epoch, rail, CXL pool, DPU profile, zpool state, and time window.

## Layer 7: Inference Runtime and Accelerator Memory

vLLM and peer runtimes consume Coherence-CE semantics. They may lookup, publish, reserve, flush, promote, and evict KV/prefix blocks through Coherence-native APIs, but they do not select physical storage or fabric resources.

Memory buffers:

| Buffer | Role |
| --- | --- |
| `kv_hbm_active` | Active decode KV in GPU HBM or equivalent accelerator memory. |
| `kv_dram_warm` | Warm host DRAM KV/prefix staging. |
| `kv_cxl_warm` | CXL T1/T1.5 warm staging when topology qualifies. |
| `kv_rdma_staging` | Registered staging region for RDMA hydration or durable write movement. |
| `vector_head_cache` | Hot vector-index heads and metadata. |
| `object_cache` | Immutable model/corpus/object cache above durable storage. |

Active decode remains HBM/local DRAM first. CXL can be used for warm state only after p99 latency, bandwidth, RAS, fabric-manager, ownership epoch, and failure-drill evidence pass.

## Layer 8: Pod Scale-Up Fabric

UA-Link or vendor-local accelerator fabrics are pod-local scale-up domains. They accelerate intra-pod accelerator communication and collective-heavy paths, but they do not replace storage fabrics.

Engineering requirements:

- define scale-up domains by pod/rack membership and failure boundary;
- keep cross-pod, storage, management, and telemetry traffic off the scale-up fabric;
- expose only capability class and health state to scheduler admission; and
- require failure drills for link, switch, endpoint, thermal, and collective-library degradation.

## Layer 9: Scale-Out RDMA/RoCEv2 Fabric

RoCEv2 is the scale-out and storage transport. It carries remote hydration, mesh replication, storage I/O, and selected object paths using UDP destination port 4791 with explicit traffic classes.

Engineering requirements:

- jumbo MTU where qualified and end-to-end consistent;
- PFC only on traffic classes that require lossless behavior;
- ECN/DCQCN thresholds by link speed, buffer profile, and workload;
- dual rails where failure-domain or bandwidth requirements justify them;
- 802.1Q trunks with explicit allowed VLANs and no implicit data native VLAN;
- separate traffic classes for frontend/API, RDMA rail-A, RDMA rail-B, storage/NVMe-oF, telemetry, timing, management, and background maintenance; and
- telemetry for PFC pause, ECN marks, CNPs, drops, queue depth, QP errors, p99 latency, FEC, and trunk member health.

## Layer 10: DPU / SmartNIC Storage Boundary

DPUs/SmartNICs are mandatory on storage-network paths. They mediate NVMe-oF, RDMA memory registration, queue pairs, tenant isolation, telemetry, and selected crypto/compression offload where qualified.

Engineering requirements:

- NVMe-oF discovery/controller service uses port 4420 on the storage plane;
- host fallback is degraded drill mode, not normal operation;
- DPU firmware/profile drift must demote admission;
- RDMA memory regions and queue pairs must be fenced on failure or tenant-boundary risk; and
- DPU metrics must roll up through Coherence-CE rather than being exposed to inference actors.

## Layer 11: OpenZFS Durable NAND Substrate

OpenZFS provides the durable NAND block substrate beneath Coherence-CE. Cross-node mirrored vdevs, checksums, snapshots, scrubs, resilvers, SLOG/L2ARC/special-vdev roles, and media endurance are storage-engineering concerns hidden from inference actors.

Engineering requirements:

- mirrored vdev legs must be independent by rack, power, switch, and rail when independence is claimed;
- synchronous durability classes must not be acknowledged until the appropriate OpenZFS/DPU durable evidence exists;
- scrub/resilver/rebuild traffic must have admission impact and traffic-class controls;
- CXL block/persistent roles require explicit media qualification before any SLOG/L2ARC/special-vdev use; and
- checksums, snapshots, import/replacement drills, and recovery evidence must be retained.

## Layer 12: Observability and Timing

The system is only safe when telemetry is fresh enough for decisions. Silence is not health.

Required observability:

| Plane | Signals |
| --- | --- |
| Coherence-CE | cache hits/misses, dirty bytes, flush age, namespace mode, index ID, durability state, admission state. |
| Runtime/GPU | HBM pressure, model residency, decode latency, KV block growth, runtime profile. |
| CXL | pool pressure, p99 latency, bandwidth, poison, RAS, ownership epoch, fabric-manager state. |
| RDMA | PFC, ECN, CNP, QP errors, drops, retransmits, p99, rail health. |
| DPU | firmware/profile, queue depth, MR/QP state, NVMe-oF state, telemetry freshness. |
| OpenZFS | zpool state, SLOG/L2ARC/special-vdev health, scrub/resilver, checksum errors, write latency. |
| Timing | PTP event/general UDP 319/320, clock quality, skew, and source state. |

Transport defaults include OTLP gRPC 4317, OTLP HTTP 4318, Prometheus 9090/9100, gNMI 9339, and PTP UDP 319/320.

## End-to-end request flow

1. OpenAI-compatible request enters the global load-balancer mesh over HTTPS 443.
2. Global policy chooses a region with acceptable service, residency, and namespace authority state.
3. Regional policy chooses a datacenter with model/KV locality and healthy Coherence-CE entrypoints.
4. Datacenter policy chooses a pod/rack/service VIP that is not RED or DRAIN.
5. Coherence-CE validates identity, namespace modality, durability class, and tenant policy.
6. Scheduler admission returns placement and deadline budget.
7. vLLM adapter receives only logical Coherence handles.
8. Active decode uses HBM/local DRAM; warm state may hydrate from DRAM/CXL/RDMA; durable state flows through DPU/OpenZFS.
9. Metrics update admission state and may trigger prewarm, throttling, drain, failover, or recompute.

## Related ADRs

- `adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md`
- `adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md`
- `adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md`
- `adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md`
- `adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md`
- `adr/ADR-014_Coherence_Metrics_Scheduler_Admission.md`
- `adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md`
- `adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md`
- `adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md`
- `adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.md`
- `adr/ADR-023_Coherence_CE_Namespace_Modalities.md`
