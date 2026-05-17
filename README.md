# Project Coherent Storage, ADR Package v4

**Project:** Project Coherent Storage
**Version:** 2026-Q2
**Package revision:** v4 UA-Link pod-scale, CXL memory pools, RDMA/RoCEv2 tuning, heterogeneous GP-GPU compute
**Generated:** 2026-05-17
**Status:** Proposed

## Purpose

This v4 package refreshes the v3 ADR set using the expanded 2026-05-17 RAG corpus and the updated `src/ADR-Storage-Reference-Arch/AGENTS.md` directives. It keeps the core v2/v3 invariant: inference actors connect to the Coherence-CE Memory Mesh and never bind directly to OpenZFS, DPU, RoCEv2, NVMe-oF, CXL, or UA-Link internals.

v4 adds a renewed architectural focus on:

1. **UA-Link enabled pod-scale systems** as a scale-up accelerator domain inside pod/rack boundaries.
2. **Network architecture across scale-up and scale-out planes**, separating UA-Link accelerator fabrics, Ethernet/RDMA scale-out, storage/NVMe-oF fabrics, management, and timing.
3. **CXL memory pools** as governed T1/T1.5 memory capacity for warm KV/prefix state, metadata, vector heads, and future shared-memory research paths.
4. **RDMA/RoCEv2 performance tuning** with explicit PFC/ECN/DCQCN, traffic-class, rail, telemetry, and failure semantics.
5. **General-purpose GPU and heterogeneous accelerator scheduling**, covering NVIDIA/AMD/Intel GPU families, cross-vendor collectives, DPU/IPU offload, CXL-GPU research, and admission-control policy.
6. **arXiv S3 bulk archive enablement**, implemented under `src/RAG-Scripts/arxiv-s3/` as credential-safe requester-pays tooling.

## v4 source basis

The v4 source pass extracted text from 363 PDFs in `src/RAG-DATA` into `project-coherent-rag-v4-text`.

- Text extraction OK: 360 PDFs
- Source map: `review-artifacts/v4-rag-extraction-and-source-map.md`

Important sources include the UA-Link white paper, UniFabriX UA-Link material, OCP Open Cluster inference/training fabric reference architectures, OCP MRC, Arista/Broadcom lossless Ethernet/RoCE material, AMD Pensando/Pollara cluster and product collateral, Intel Gaudi 3 cluster design, CXL/KV/GPU research, and prior Marvell/XConn/CXL/DPU materials.

## Package index

| Path | Purpose |
| --- | --- |
| `reports/ualink-pod-scale-cxl-rdma-gpgpu-v4.md` | Main v4 architecture report. |
| `adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md` | New ADR for UA-Link pod-scale scale-up domains. |
| `adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md` | New ADR for scale-out/storage networking and RoCEv2 tuning. |
| `adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.md` | New ADR for CXL pool semantics in UA-Link pods. |
| `adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md` | New ADR for heterogeneous GPU/accelerator scheduling. |
| `diagrams/v4-*.puml`, `.png`, `.svg` | v4 PlantUML source and renders. |
| `review-artifacts/v4-rag-extraction-and-source-map.*` | Extraction evidence and source map. |

## ADR index

ADR-001 through ADR-017 are inherited from v3 with v4 notes appended where lower-layer behavior changes. New v4 ADRs are:

| ADR | Title | Decision summary |
| --- | --- | --- |
| ADR-018 | UA-Link Pod-Scale Fabric and Compute Domains | Treat UA-Link as a pod/rack-scale accelerator scale-up fabric below Coherence-CE and scheduler policy, not as an actor-visible API. |
| ADR-019 | Pod-Scale Network Architecture and RDMA/RoCEv2 Tuning | Define separate UA-Link, scale-out RDMA, storage/NVMe-oF, management, and timing planes with explicit RoCEv2 tuning gates. |
| ADR-020 | CXL Memory Pools for UA-Link Pods | Govern CXL memory pools as T1/T1.5 warm memory behind Coherence-CE with fabric-manager, ownership, latency, and failure evidence. |
| ADR-021 | Heterogeneous GP-GPU Compute and Scheduler Governance | Admit NVIDIA, AMD, Intel, DPU/IPU, FPGA/NPU, and edge accelerators through capability profiles, not vendor assumptions. |

## arXiv S3 tooling

Credential-safe requester-pays S3 tools were added at:

`src/RAG-Scripts/arxiv-s3/`

They support manifest fetch, manifest indexing, full/targeted/monthly download planning, raw tar retention, full explosion of PDF/source tar chunks, PDF text extraction, and validation reporting. Downloading waits on AWS requester-pays credentials and AWS CLI installation.

## Public claim guardrail

UA-Link, CXL, RoCEv2, DPU, and heterogeneous GPU claims must use the v3/v4 evidence-grade rule:

- Direct: source explicitly states the relationship or capability.
- Adjacent: relevant to architecture but not proof of a named integration.
- Negative-control: retained to prevent overclaiming.
- Not found in current sweep: searched but no direct source-backed mention found.
