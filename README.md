# Project Coherent Storage ADR Package v4

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
6. **arXiv S3 bulk archive enablement**, implemented under `../RAG-Scripts/arxiv-s3/` as credential-safe requester-pays tooling.

## v4 source basis

The v4 source pass extracted text from 363 PDFs in `/home/cdex-routeros/src/RAG-DATA` into `/tmp/project-coherent-rag-v4-text`.

- Text extraction OK: 360 PDFs
- Text extraction failed: 3 PDFs
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

| ADR File | Document Function |
| --- | --- |
| [`ADR-001_Inference_Storage_Principles_and_SLOs.md`](adr/ADR-001_Inference_Storage_Principles_and_SLOs.md) | Defines inference-first storage principles, latency SLOs, tier boundaries, and workload classes that govern all later ADRs. |
| [`ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md`](adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md) | Defines the hot KV/prefix-cache data plane and keeps inference actors behind the Coherence-CE Memory Mesh. |
| [`ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md`](adr/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md) | Defines model-weight, adapter, tokenizer, object, corpus, and artifact tiers for reproducible inference data placement. |
| [`ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md`](adr/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md) | Defines RDMA, RoCEv2, GPU-direct, and scale-out data-path rules for cross-node inference and storage movement. |
| [`ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md`](adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md) | Defines mandatory DPU/SmartNIC offload boundaries for NVMe-oF, RDMA mediation, isolation, telemetry, and degraded host fallback. |
| [`ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md`](adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md) | Defines OpenZFS, NVMe-oF, mirrored NAND, media layout, and durable block-substrate rules. |
| [`ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md`](adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md) | Defines scheduler admission using model, KV, fabric, CXL, DPU, rail, and locality telemetry. |
| [`ADR-008_RAG_Vector_Index_and_Corpus_Service.md`](adr/ADR-008_RAG_Vector_Index_and_Corpus_Service.md) | Defines immutable RAG corpus, embedding, vector-index, retrieval-cache, and corpus-service architecture. |
| [`ADR-009_Observability_Benchmarking_and_Rollout_Gates.md`](adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.md) | Defines observability, benchmark, failure-drill, and rollout gates for inference, fabric, storage, CXL, and scheduler claims. |
| [`ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md`](adr/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md) | Defines Coherence-CE write-through, write-back, write-around, and write-behind policy to OpenZFS by durability class. |
| [`ADR-011_KV_Durability_Classes.md`](adr/ADR-011_KV_Durability_Classes.md) | Defines KV-D0 through KV-D5 durability classes used by Coherence-CE, OpenZFS write policy, failure recovery, and scheduler admission. |
| [`ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md`](adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md) | Defines the Coherence-native and OpenAI-compatible API contract exposed to vLLM adapters without leaking lower-layer storage or fabric. |
| [`ADR-013_Failure_Semantics_and_Fencing.md`](adr/ADR-013_Failure_Semantics_and_Fencing.md) | Defines failure semantics, fencing, recovery, drain behavior, and degraded-mode rules across compute, fabric, DPU, CXL, and storage. |
| [`ADR-014_Coherence_Metrics_Scheduler_Admission.md`](adr/ADR-014_Coherence_Metrics_Scheduler_Admission.md) | Defines how Coherence-CE metrics roll up into scheduler GREEN, AMBER, RED, and DRAIN admission states. |
| [`ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md`](adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md) | Defines CXL T1/T1.5 memory tiering, memory-pool governance, and safe OpenZFS-adjacent CXL roles. |
| [`ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md`](adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md) | Defines evidence grades and public-claim guardrails for vendor roadmap, partnership, and integration statements. |
| [`ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md`](adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md) | Defines research metadata, arXiv API/bulk-data, Markdown, LaTeX, BibTeX, and publication workflow requirements. |
| [`ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md`](adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md) | Defines UA-Link pod-scale accelerator fabric domains and their scheduler-visible but actor-hidden compute locality semantics. |
| [`ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md`](adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md) | Defines pod-scale network planes and RDMA/RoCEv2 tuning gates for traffic classes, PFC, ECN/DCQCN, rails, and telemetry. |
| [`ADR-020_CXL_Memory_Pools_for_UALink_Pods.md`](adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.md) | Defines CXL memory pools inside UA-Link pods as governed Coherence-owned warm capacity with ownership, latency, and failure gates. |
| [`ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md`](adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md) | Defines heterogeneous GP-GPU and accelerator capability profiles for scheduler governance across vendors and fabrics. |

## Top-down architecture composition

The v4 design composes the system from inference SLOs down through hot-state placement, data tiers, fabrics, offload, durable media, scheduler admission, failure semantics, CXL/UA-Link pod resources, heterogeneous accelerator governance, and research-publication workflow. Each ADR has a PlantUML source file plus PNG/SVG renders under `diagrams/adr/`.

| ADR | Architecture interaction diagram |
| --- | --- |
| [`ADR-001_Inference_Storage_Principles_and_SLOs.md`](adr/ADR-001_Inference_Storage_Principles_and_SLOs.md) | [PNG](diagrams/adr/ADR-001_Inference_Storage_Principles_and_SLOs.png) / [SVG](diagrams/adr/ADR-001_Inference_Storage_Principles_and_SLOs.svg) / [PUML](diagrams/adr/ADR-001_Inference_Storage_Principles_and_SLOs.puml) |
| [`ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md`](adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md) | [PNG](diagrams/adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.png) / [SVG](diagrams/adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.svg) / [PUML](diagrams/adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.puml) |
| [`ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md`](adr/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md) | [PNG](diagrams/adr/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.png) / [SVG](diagrams/adr/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.svg) / [PUML](diagrams/adr/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.puml) |
| [`ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md`](adr/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md) | [PNG](diagrams/adr/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.png) / [SVG](diagrams/adr/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.svg) / [PUML](diagrams/adr/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.puml) |
| [`ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md`](adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md) | [PNG](diagrams/adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.png) / [SVG](diagrams/adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.svg) / [PUML](diagrams/adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.puml) |
| [`ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md`](adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md) | [PNG](diagrams/adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.png) / [SVG](diagrams/adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.svg) / [PUML](diagrams/adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.puml) |
| [`ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md`](adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md) | [PNG](diagrams/adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.png) / [SVG](diagrams/adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.svg) / [PUML](diagrams/adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.puml) |
| [`ADR-008_RAG_Vector_Index_and_Corpus_Service.md`](adr/ADR-008_RAG_Vector_Index_and_Corpus_Service.md) | [PNG](diagrams/adr/ADR-008_RAG_Vector_Index_and_Corpus_Service.png) / [SVG](diagrams/adr/ADR-008_RAG_Vector_Index_and_Corpus_Service.svg) / [PUML](diagrams/adr/ADR-008_RAG_Vector_Index_and_Corpus_Service.puml) |
| [`ADR-009_Observability_Benchmarking_and_Rollout_Gates.md`](adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.md) | [PNG](diagrams/adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.png) / [SVG](diagrams/adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.svg) / [PUML](diagrams/adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.puml) |
| [`ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md`](adr/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md) | [PNG](diagrams/adr/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.png) / [SVG](diagrams/adr/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.svg) / [PUML](diagrams/adr/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.puml) |
| [`ADR-011_KV_Durability_Classes.md`](adr/ADR-011_KV_Durability_Classes.md) | [PNG](diagrams/adr/ADR-011_KV_Durability_Classes.png) / [SVG](diagrams/adr/ADR-011_KV_Durability_Classes.svg) / [PUML](diagrams/adr/ADR-011_KV_Durability_Classes.puml) |
| [`ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md`](adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md) | [PNG](diagrams/adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.png) / [SVG](diagrams/adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.svg) / [PUML](diagrams/adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.puml) |
| [`ADR-013_Failure_Semantics_and_Fencing.md`](adr/ADR-013_Failure_Semantics_and_Fencing.md) | [PNG](diagrams/adr/ADR-013_Failure_Semantics_and_Fencing.png) / [SVG](diagrams/adr/ADR-013_Failure_Semantics_and_Fencing.svg) / [PUML](diagrams/adr/ADR-013_Failure_Semantics_and_Fencing.puml) |
| [`ADR-014_Coherence_Metrics_Scheduler_Admission.md`](adr/ADR-014_Coherence_Metrics_Scheduler_Admission.md) | [PNG](diagrams/adr/ADR-014_Coherence_Metrics_Scheduler_Admission.png) / [SVG](diagrams/adr/ADR-014_Coherence_Metrics_Scheduler_Admission.svg) / [PUML](diagrams/adr/ADR-014_Coherence_Metrics_Scheduler_Admission.puml) |
| [`ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md`](adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md) | [PNG](diagrams/adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.png) / [SVG](diagrams/adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.svg) / [PUML](diagrams/adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.puml) |
| [`ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md`](adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md) | [PNG](diagrams/adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.png) / [SVG](diagrams/adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.svg) / [PUML](diagrams/adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.puml) |
| [`ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md`](adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md) | [PNG](diagrams/adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.png) / [SVG](diagrams/adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.svg) / [PUML](diagrams/adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.puml) |
| [`ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md`](adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md) | [PNG](diagrams/adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.png) / [SVG](diagrams/adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.svg) / [PUML](diagrams/adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.puml) |
| [`ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md`](adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md) | [PNG](diagrams/adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.png) / [SVG](diagrams/adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.svg) / [PUML](diagrams/adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.puml) |
| [`ADR-020_CXL_Memory_Pools_for_UALink_Pods.md`](adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.md) | [PNG](diagrams/adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.png) / [SVG](diagrams/adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.svg) / [PUML](diagrams/adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.puml) |
| [`ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md`](adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md) | [PNG](diagrams/adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.png) / [SVG](diagrams/adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.svg) / [PUML](diagrams/adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.puml) |

## ADR diagram gallery

### [ADR-001_Inference_Storage_Principles_and_SLOs.md](adr/ADR-001_Inference_Storage_Principles_and_SLOs.md)

![ADR-001_Inference_Storage_Principles_and_SLOs](diagrams/adr/ADR-001_Inference_Storage_Principles_and_SLOs.png)

### [ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md](adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md)

![ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane](diagrams/adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.png)

### [ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md](adr/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md)

![ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers](diagrams/adr/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.png)

### [ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md](adr/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md)

![ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths](diagrams/adr/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.png)

### [ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md](adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md)

![ADR-005_DPU_and_SmartNIC_Offload_Boundaries](diagrams/adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.png)

### [ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md](adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md)

![ADR-006_OpenZFS_NVMe_oF_and_Media_Layout](diagrams/adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.png)

### [ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md](adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md)

![ADR-007_Inference_Scheduler_Locality_and_Admission_Control](diagrams/adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.png)

### [ADR-008_RAG_Vector_Index_and_Corpus_Service.md](adr/ADR-008_RAG_Vector_Index_and_Corpus_Service.md)

![ADR-008_RAG_Vector_Index_and_Corpus_Service](diagrams/adr/ADR-008_RAG_Vector_Index_and_Corpus_Service.png)

### [ADR-009_Observability_Benchmarking_and_Rollout_Gates.md](adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.md)

![ADR-009_Observability_Benchmarking_and_Rollout_Gates](diagrams/adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.png)

### [ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md](adr/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md)

![ADR-010_Coherence_CE_Write_Policy_to_OpenZFS](diagrams/adr/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.png)

### [ADR-011_KV_Durability_Classes.md](adr/ADR-011_KV_Durability_Classes.md)

![ADR-011_KV_Durability_Classes](diagrams/adr/ADR-011_KV_Durability_Classes.png)

### [ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md](adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md)

![ADR-012_Coherence_CE_vLLM_Adapter_API_Contract](diagrams/adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.png)

### [ADR-013_Failure_Semantics_and_Fencing.md](adr/ADR-013_Failure_Semantics_and_Fencing.md)

![ADR-013_Failure_Semantics_and_Fencing](diagrams/adr/ADR-013_Failure_Semantics_and_Fencing.png)

### [ADR-014_Coherence_Metrics_Scheduler_Admission.md](adr/ADR-014_Coherence_Metrics_Scheduler_Admission.md)

![ADR-014_Coherence_Metrics_Scheduler_Admission](diagrams/adr/ADR-014_Coherence_Metrics_Scheduler_Admission.png)

### [ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md](adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md)

![ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction](diagrams/adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.png)

### [ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md](adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md)

![ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails](diagrams/adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.png)

### [ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md](adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md)

![ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow](diagrams/adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.png)

### [ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md](adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md)

![ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains](diagrams/adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.png)

### [ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md](adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md)

![ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning](diagrams/adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.png)

### [ADR-020_CXL_Memory_Pools_for_UALink_Pods.md](adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.md)

![ADR-020_CXL_Memory_Pools_for_UALink_Pods](diagrams/adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.png)

### [ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md](adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md)

![ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance](diagrams/adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.png)


## arXiv S3 tooling

Credential-safe requester-pays S3 tools were added at:

`/home/cdex-routeros/src/RAG-Scripts/arxiv-s3/`

They support manifest fetch, manifest indexing, full/targeted/monthly download planning, raw tar retention, full explosion of PDF/source tar chunks, PDF text extraction, and validation reporting. Downloading waits on AWS requester-pays credentials and AWS CLI installation.

## Public claim guardrail

UA-Link, CXL, RoCEv2, DPU, and heterogeneous GPU claims must use the v3/v4 evidence-grade rule:

- Direct: source explicitly states the relationship or capability.
- Adjacent: relevant to architecture but not proof of a named integration.
- Negative-control: retained to prevent overclaiming.
- Not found in current sweep: searched but no direct source-backed mention found.
