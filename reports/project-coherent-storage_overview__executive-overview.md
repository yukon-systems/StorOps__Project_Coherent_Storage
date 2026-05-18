# Project Coherent Storage Overview: Executive Overview

**Project:** Project Coherent Storage
**Audience:** Executive overview
**Architecture cycle:** 2026-Q2
**Generated:** 2026-05-18
**Status:** Proposed training/report draft

## Executive premise

Project Coherent Storage is an inference-first storage architecture. vLLM and other inference actors do not bind to OpenZFS, DPU, NVMe-oF, RoCEv2, RDMA, CXL, or UA-Link directly. They bind to the Coherence-CE Memory Mesh, which owns KV/prefix-cache placement, durability classes, object/API translation, and scheduler-visible metrics.

Beneath Coherence-CE, OpenZFS nodes provide the durable NAND block substrate, DPUs/SmartNICs mediate NVMe-oF/RDMA/storage-network offload, and CXL may provide governed memory expansion, warm KV/prefix staging, metadata memory, and future pooled-memory roles when topology and telemetry qualify.

## What leaders should remember

1. **Coherence-CE is the API and policy boundary.** Inference actors see Coherence-CE semantics, not CXL/OpenZFS/RDMA/DPU internals.
2. **DPUs remain a hard storage-network requirement.** NVMe-oF/RDMA offload, tenant boundary enforcement, telemetry, memory registration pressure, and storage-path isolation require DPU/SmartNIC hardware.
3. **CXL addresses memory pressure, not durable storage by default.** It can reduce repeated hydration and improve warm-state economics, but it does not replace GPU HBM, local DRAM, OpenZFS durable NAND, or DPU offload.
4. **Namespace modality matters for global scale.** Unified Namespace simplifies clients; Dimensional Indexed Namespace bounds inter-datacenter lookup, search, and invalidation latency.
5. **Roadmap evidence must be graded.** Public-facing claims must separate direct evidence from adjacent ecosystem evidence and from unverified integrations.

## Executive decision points

| Decision | Recommended posture | Rationale |
| --- | --- | --- |
| Include CXL in architecture roadmap? | Yes, as governed memory capacity. | It can relieve warm KV/prefix, metadata, and vector-head pressure when telemetry qualifies. |
| Claim CXL is production hot path? | No. | KV-D0 active decode remains GPU HBM/local DRAM-first unless local evidence proves otherwise. |
| Require DPUs? | Yes. | Storage-network offload and RDMA/NVMe-oF mediation are core requirements. |
| Support dual namespace models? | Yes. | Unified Namespace is simple; Dimensional Indexed Namespace controls locality and blast radius. |
| Publish externally? | Yes, with evidence-grade language. | Public documents must separate direct evidence from adjacent or inferred architecture recommendations. |
| Invest in lab validation? | Yes. | Vendor roadmaps do not substitute for p99 latency, bandwidth, RAS, and failure-drill evidence. |

## Business value

- Better accelerator utilization by reducing avoidable cold starts and repeated prefix/KV hydration.
- Lower overprovisioning risk through scheduler-visible memory, fabric, DPU, CXL, and storage-health metrics.
- Reduced cross-datacenter cache latency through dimensional locality indexes where global lookup is too expensive.
- Safer public roadmap communication through claim grading and reproducible RAG/source archives.

## Residual executive risks

| Risk | Mitigation |
| --- | --- |
| CXL is treated as universal hot-path memory. | Keep CXL in governed T1/T1.5 roles until local SLO evidence permits narrower use. |
| DPU fallback becomes normal operation. | Treat host fallback as degraded drill mode with audit, rate limits, and rollback gates. |
| Global cache namespace causes latency or invalidation blast radius. | Use Dimensional Indexed Namespace for region/datacenter/pod-local authority. |
| Vendor roadmap claims outpace evidence. | Enforce ADR-016 evidence grades before reports, presentations, or arXiv publication. |

## Source anchors

This overview is derived from the ADR package, `review-artifacts/rag-extraction-and-source-map.md`, `latex/references.bib`, and the architecture reports in `reports/`.
