# Project Coherent Storage Overview: Director Overview

**Project:** Project Coherent Storage
**Audience:** Director review
**Architecture cycle:** 2026-Q2
**Generated:** 2026-05-18
**Status:** Proposed training/report draft

## Director review objective

Director-level review should focus on procurement, lifecycle, deployment risk, staffing, and operational readiness. The architecture is not a single storage product; it is a governed stack where Coherence-CE controls actor-visible semantics and lower layers provide qualified capacity, locality, durability, offload, and telemetry.

## Operating model

Review these decisions before purchase or deployment:

- CPU platform, firmware, kernel, and BIOS support for CXL memory expansion and pooling.
- Slot/root-complex placement for CXL memory, GPU, DPU, NIC, and NVMe devices.
- DPU/SmartNIC qualification for NVMe-oF, RDMA, tenant isolation, telemetry, and host fallback.
- OpenZFS node layout: mirrored NAND block tier, SLOG/L2ARC/special-vdev qualification, scrub/resilver impact.
- Network segmentation: frontend/API, management, timing, telemetry, RDMA rail-A, RDMA rail-B, storage/NVMe-oF, and background maintenance classes.
- Namespace operating model: Unified Namespace for simple global identity; Dimensional Indexed Namespace for bounded locality authority.
- Coherence-CE metrics integration with scheduler admission.
- Evidence-grade public communication.

## Procurement matrix

| Component | Required evidence before purchase | Governance note |
| --- | --- | --- |
| CXL memory expansion | CPU/root-complex support, BIOS/firmware, Linux CXL driver support, NUMA topology, telemetry endpoint. | Do not buy capacity without lane/topology placement evidence. |
| CXL switch/fabric | Switch generation, hop count, CFM/fabric manager, pool ownership epoch, p99 latency, RAS counters. | Treat as T1.5 warm/shared memory first, not active decode or durability. |
| DPU/SmartNIC | NVMe-oF/RDMA offload, memory-registration handling, tenant isolation, telemetry, host fallback. | Required for storage network paths. |
| NVMe media | Endurance, flush semantics, power-loss protection, mirrored vdev plan, rebuild behavior. | OpenZFS durability depends on media semantics, not roadmap claims. |
| Ethernet/RDMA switching | RoCEv2 profile, PFC scope, ECN/DCQCN, telemetry, FEC, MTU, rail isolation. | Lossless configuration is a controlled architecture surface, not a post-install knob. |
| Retimers/switches | PCIe/CXL generation, signal integrity, error telemetry, topology visibility. | Avoid hidden switch/bifurcation for latency-sensitive paths. |

## Namespace modality decision

| Question | Prefer Unified Namespace | Prefer Dimensional Indexed Namespace |
| --- | --- | --- |
| Client simplicity is the highest priority? | Yes. | No. |
| Cache operations are mostly local or low fan-out? | Yes. | Not necessarily. |
| Cross-datacenter latency must be bounded? | Only with internal routing guarantees. | Yes. |
| Invalidation blast radius must be constrained? | Harder. | Yes. |
| Scheduler needs locality-scoped admission? | Limited. | Yes. |
| Transaction locality changes over time? | Coherence hides it. | Use `locality_epoch` and index rotation. |

## Roadmap report inclusions

Use these categories in roadmap material:

1. **CXL memory expansion and pooling:** capacity expansion, fabric management, pool ownership, RAS, telemetry, and root-complex placement.
2. **DPU/SmartNIC offload:** NVMe-oF/RDMA path mediation, tenant isolation, telemetry, crypto/compression where qualified, and degraded host fallback.
3. **RDMA/RoCEv2 fabrics:** lossless class scoping, ECN/DCQCN, MTU/FEC, trunking, rails, failure domains, and p99 validation.
4. **OpenZFS substrate:** mirrored NAND, checksum behavior, scrub/resilver gates, SLOG/L2ARC/special-vdev qualification, and DPU-mediated NVMe-oF.
5. **Coherence-CE mesh:** durability classes, namespace modality, metrics rollup, and scheduler admission.
6. **Evidence governance:** direct, adjacent, negative-control, and not-found claim grades.

## Director readiness checklist

- [ ] DPU storage paths are mandatory in the bill of materials and qualification plan.
- [ ] CXL devices have explicit topology, root-complex, and telemetry evidence.
- [ ] RDMA traffic classes and VLAN/rail isolation are documented before deployment.
- [ ] OpenZFS mirror/failure domains do not share a rack, power, switch, or rail failure domain where independence is claimed.
- [ ] Namespace modality is selected per workload and tenant locality profile.
- [ ] Coherence-CE metrics can drive scheduler GREEN/AMBER/RED/DRAIN admission.
- [ ] Public claims use ADR-016 evidence-grade rules.

## Source anchors

This overview is derived from the ADR package, `review-artifacts/rag-extraction-and-source-map.md`, `latex/references.bib`, and the architecture reports in `reports/`.
