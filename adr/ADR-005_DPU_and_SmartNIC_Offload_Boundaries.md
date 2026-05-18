# ADR-005: DPU and SmartNIC Offload Boundaries

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Require DPU/SmartNIC hardware on storage-network paths for NVMe-oF hardware offload, RDMA memory/resource mediation, tenant isolation, encryption, and telemetry, while preserving host fallback as a degraded/resilience path and keeping durable authority outside the DPU.

## Context

The baseline package treated DPU/SmartNIC offload as a storage acceleration and isolation capability. This refresh tightens the requirement: DPU/SmartNIC hardware is mandatory on the storage data plane because Project Coherent Storage depends on hardware offload for NVMe-oF and controlled handling of RDMA memory, queue pairs, and tenant capabilities across storage network paths. The RAG corpus still adds caution: DPUs are heterogeneous, memory-limited, vendor-specific, and often harder to program and observe than hosts. Research systems show strong value in offloading reads, data movement, encryption, and RDMA resource control to the DPU, but they also emphasize that writes, complex coordination, and large caches often remain better suited to the host. The newer OCP management references add a second constraint: DPU/SmartNIC offload must be visible through standard platform-management and low-latency management channels, not just vendor tools.

The post-refresh Intel BMRA and QAT sources add a host/platform accelerator distinction. Intel QAT can accelerate cryptographic and compression services on supported hosts through integrated, PCIe AIC, PF, or VF exposure, and BMRA-style automation shows how such accelerators are prepared through BIOS, kernel boot parameters, SR-IOV/IOMMU, device plugins, telemetry-aware scheduling, and Ansible. QAT is not a DPU/SmartNIC replacement: it does not provide NVMe-oF/RDMA storage-path mediation, rkey/capability governance, or fabric isolation. QAT must therefore be governed as a local trusted accelerator beneath Coherence-CE policy and above the hardware trust boundary, with stricter virtualization and trust gates than ordinary CPU fallback.

## Decision

- DPUs are required storage-path hardware, data-path accelerators, and isolation boundaries; they are not the durable source of truth.
- Require DPU/SmartNIC hardware for:
  - NVMe-oF target/initiator hardware offload on storage network paths.
  - RDMA memory registration, rkey/capability lifetime control, queue-pair/resource mediation, and tenant isolation.
  - RDMA object client or gateway acceleration.
  - Encryption/decryption and checksum offload where latency and telemetry gates pass.
  - Packet classification, QoS marking, congestion/fabric telemetry, and storage-path observability.
  - Metadata fast paths for read-mostly services only when qualified; durable metadata authority remains off-DPU.
- Keep authoritative metadata, placement maps, model manifests, policy, and audit state in central or replicated host services.
- Require host-based fallback for every production storage namespace and inference data service, but treat fallback as degraded/resilience operation rather than the normal architecture.
- Treat each DPU model and firmware line as a separate qualification target.
- Record the DPU/SmartNIC management path, DC-SCM/OBMF exposure where applicable, and low-latency management-channel health before enabling production-like offload.
- Treat CXL, GPU, DPU, NIC, and NVMe slot placement as one shared root-complex/lane-governance decision; DPU-adjacent staging buffers may use CXL only when topology and latency are qualified.
- Treat Intel QAT as a separate host/platform cryptographic and compression accelerator:
  - allowed for TLS/IPsec/compression/helper paths only when driver, firmware, BIOS, SR-IOV, VF/PF, trust boundary, and telemetry gates pass;
  - forbidden as a substitute for DPU/SmartNIC NVMe-oF/RDMA offload;
  - forbidden for untrusted guest or untrusted userspace-direct exposure;
  - required to fall back to CPU/host software or drain when QAT endpoint, VF/PF, driver, or firmware health is ambiguous.

## Offload boundary

| Function | Default execution location | Reason |
| --- | --- | --- |
| KV placement metadata quorum | Host/control services | Requires durable authority and flexible coordination |
| NVMe-oF storage data path | Required DPU/SmartNIC hardware with qualified host fallback | Hardware offload and RDMA resource mediation are core requirements; fallback is degraded/resilience mode |
| Hot KV data movement | DPU/SmartNIC path where qualified, host fallback for degradation | DPU controls RDMA resources and reduces host CPU while cache semantics stay above the block tier |
| Immutable model/object reads | DPU-required storage-path hardware, service profile qualified per platform | Read-heavy and transport-friendly |
| Writes to durable object/ZFS tier | Host or host-coordinated DPU path | Requires ordering, checksums, snapshots, and recovery semantics |
| Encryption and tenant ACL | DPU-preferred with host policy authority | Keeps keys and enforcement close to ingress/data path |
| RDMA QP/resource isolation | DPU-preferred | Prevents direct untrusted tenant access to RNIC resources |
| Observability export | DPU plus host collector | DPU state must not be invisible |
| Management access | DC-SCM/OBMF/BMC or vendor-equivalent path plus host collector | Offload must remain operable and observable during data-path faults |
| CXL-backed staging buffers | Host DRAM first; CXL only when same-root-complex/NUMA placement is qualified | DPU memory remains scarce; CXL can relieve host pressure but hidden switching or cross-socket paths can erase offload benefit |
| QAT crypto/compression acceleration | Host/platform accelerator, optionally exposed to trusted guests/driver domains through qualified SR-IOV/VF/PF policy | Useful for TLS/IPsec/compression assist but not an RDMA/NVMe-oF offload boundary or durable authority |

## RDMA primitive policy

- One-sided RDMA is allowed for trusted, registered, immutable or read-mostly data regions with explicit capability lifetime.
- Two-sided RDMA or DPU-mediated request handling is preferred when receiver ownership, buffer reuse, tenant isolation, or ordering matters.
- RDMA rkeys, memory windows, and queue-pair capabilities must be short-lived, auditable, and revocable.
- DPU/gateway mediation is mandatory for multi-tenant direct access unless the tenant is fully trusted and isolated at the fabric/security layer.

## Positive consequences

- Host CPU cycles are preserved for inference, scheduling, and storage coordination.
- Tenant boundaries are clearer than exposing raw RNIC access to workloads.
- DPU offload can be adopted incrementally by service and hardware profile.
- Host fallback prevents DPU firmware or SDK issues from becoming storage-wide outages.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| DPU firmware or SDK drift creates unrepeatable behavior | Pin firmware/driver/SDK versions in source-of-truth and gate upgrades with canary tests. |
| DPU memory is too small for metadata or cache workloads | Keep large metadata and cache state on host DRAM or qualified same-root-complex CXL/T2; use DPU for fast-path mediation. |
| Offload hides telemetry | Block production-like use until DPU metrics include CPU, memory, queues, link state, drops, errors, and service health. |
| Vendor lock-in | Keep service API above DPU-specific SDKs and preserve host fallback. |
| Host fallback is mistaken for normal architecture | Document fallback as degraded/resilience mode and require DPU/SmartNIC readiness before production-like storage-path admission. |
| Management-plane blind spot | Require a documented platform-management path and heartbeat for each offload service before admission. |
| CXL placement steals lanes or adds hidden switch latency to DPU/GPU paths | Co-design CXL/GPU/DPU/NIC/NVMe placement; reject switched or auto-bifurcated CXL for latency-sensitive offload/staging roles unless measured and explicitly qualified. |
| QAT is exposed to an untrusted VM or userspace process | Permit QAT SR-IOV/VF/PF exposure only to trusted guests or driver domains; protect driver, firmware, and device files; block userspace-direct access for untrusted workloads. |
| QAT endpoint/VF/PF reset disrupts other guests or workloads | Treat QAT reset, host driver removal, VF/PF reprovisioning, and `qat_service` transitions as drain-required operations with guest shutdown/quiesce gates and recovery evidence. |
| QAT is mistaken for a DPU | Document QAT as local crypto/compression acceleration only; storage-path RDMA/NVMe-oF mediation remains DPU/SmartNIC-owned. |

## Acceptance criteria

- Each storage-network path has an assigned DPU/SmartNIC hardware profile with firmware, driver, SDK, offload services, telemetry endpoints, and fallback path.
- A canary namespace runs through the DPU/SmartNIC NVMe-oF path by default and can move to host-assisted fallback without changing object IDs or NVMe namespace identity.
- DPU-mediated tenant access rejects unauthorized RDMA capabilities and demonstrates bounded rkey/capability lifetime.
- DPU failure triggers failover or fallback without losing durable metadata.
- DPU telemetry is visible in the inference/storage dashboard before workload admission.
- A management-path drill proves DPU/offload service state can be inspected or disabled when the data path is degraded.
- Hardware inventory records DPU, GPU, NIC, NVMe, and CXL slot/root-complex ownership, link width/speed, switch hop count, and bifurcation state before enabling DPU-adjacent CXL staging.
- Any QAT-enabled profile records QAT device model, integrated/AIC form, PF/VF mapping, SR-IOV trust boundary, BIOS/firmware, driver package, kernel version, VM machine type, telemetry endpoint, and CPU fallback path.
- QAT passthrough or VF assignment is qualified only for trusted guests/driver domains, and tests prove host driver removal/reset does not occur while guest VFs are active.

## Source documents

| ID | Use |
| --- | --- |
| A0 | Existing DPU/SmartNIC storage offload baseline. |
| R05 | RDMA-first object storage with SmartNIC offloaded client/data plane. |
| R06 | DDS division of read offload to DPU and complex writes to host. |
| R07 | DPU-mediated RDMA isolation and zero-copy multi-node data plane. |
| R08, R09 | DPU engines, abstraction mismatch, heterogeneity, and operational constraints. |
| R15 | RDMA primitive and memory-management implications. |
| R33, R40 | OCP platform-management and OBMF interface-consolidation references for observable, resilient offload management paths. |
| R34 | OCP inference fabric profile requiring Day-2 lifecycle observability for fabric-attached services. |
| R28, R29, O10, O11 | CXL memory expansion/topology context used to govern DPU-adjacent staging and lane placement. |
| R251 | Intel BMRA reference architecture automation, BIOS, SR-IOV/IOMMU, device-plugin, telemetry-aware scheduling, and QAT deployment context. |
| R252 | Intel QAT release notes for supported hardware, crypto/compression services, Xen/SR-IOV limits, trust assumptions, reset/driver hazards, and virtualization caveats. |
| ADR-015 | CXL placement and role-governance rules that constrain DPU/GPU/NVMe slot decisions. |

## Pod-scale update: DPU/IPU placement in pod-scale storage fabrics

The pod-scale update keeps DPU/SmartNIC hardware mandatory for storage-network paths and adds pod-local placement requirements. DPU/IPU devices must be inventoried with GPU/NIC/CXL/root-complex locality, storage/NVMe-oF queue ownership, RDMA memory registration behavior, isolation policy, telemetry endpoint, and failover class. Host fallback remains a degraded resilience path, not the normal production data path.
