# Project Coherent Storage ADR Package

**Project:** Project Coherent Storage
**Architecture cycle:** 2026-Q2
**Architecture focus:** Coherence-CE namespace modalities, UA-Link pod-scale systems, CXL memory pools, RDMA/RoCEv2 tuning, DPU-offloaded OpenZFS storage, heterogeneous GP-GPU compute
**Generated:** 2026-05-18
**Status:** Proposed

## Purpose

This package refreshes the ADR set using the expanded RAG corpus and the project directives. It keeps the core invariant: inference actors connect to the Coherence-CE Memory Mesh and never bind directly to OpenZFS, DPU, RoCEv2, NVMe-oF, CXL, UA-Link, VLANs, RDMA memory handles, or physical storage internals.

The architecture emphasizes:

1. **Coherence-CE namespace modalities** with explicit Unified Namespace and Dimensional Indexed Namespace workflows for scalable cache locality.
2. **UA-Link enabled pod-scale systems** as a scale-up accelerator domain inside pod/rack boundaries.
3. **Network architecture across scale-up and scale-out planes**, separating UA-Link accelerator fabrics, Ethernet/RDMA scale-out, storage/NVMe-oF fabrics, management, telemetry, and timing.
4. **CXL memory pools** as governed T1/T1.5 memory capacity for warm KV/prefix state, metadata, vector heads, and future shared-memory research paths.
5. **RDMA/RoCEv2 performance tuning** with explicit PFC/ECN/DCQCN, traffic-class, rail, telemetry, and failure semantics.
6. **DPU/SmartNIC storage offload** as a hard requirement for NVMe-oF/RDMA storage-network paths.
7. **General-purpose GPU and heterogeneous accelerator scheduling**, covering vendor capability profiles and admission-control policy.
8. **arXiv S3 bulk archive enablement**, implemented under `RAG-Scripts/arxiv-s3/` as credential-safe requester-pays tooling.

## Source basis

The source pass extracted text from 363 PDFs in the `RAG-DATA/` corpus into a local processing cache.

- Text extraction OK: 360 PDFs
- Text extraction failed: 3 PDFs
- Source map: `review-artifacts/rag-extraction-and-source-map.md`

Important sources include the UA-Link white paper, UniFabriX UA-Link material, OCP Open Cluster inference/training fabric reference architectures, OCP MRC, Arista/Broadcom lossless Ethernet/RoCE material, AMD Pensando/Pollara cluster and product collateral, Intel Gaudi 3 cluster design, CXL/KV/GPU research, and prior Marvell/XConn/CXL/DPU materials.

## Package index

| Path | Purpose |
| --- | --- |
| [`reports/project-coherent-storage_architecture-report.md`](reports/project-coherent-storage_architecture-report.md) | Main architecture report for UA-Link pod scale, CXL memory pools, RDMA/RoCEv2, and heterogeneous GP-GPU compute. |
| [`reports/project-coherent-storage_engineering-deep-dive.md`](reports/project-coherent-storage_engineering-deep-dive.md) | Top-down engineering deep-dive from OpenAI/user layer through global/regional/datacenter load-balancer meshes and intra-datacenter storage layers. |
| [`reports/project-coherent-storage_overview__executive-overview.md`](reports/project-coherent-storage_overview__executive-overview.md) | Executive overview for business value, hard requirements, namespace posture, and residual risks. |
| [`reports/project-coherent-storage_overview__director-overview.md`](reports/project-coherent-storage_overview__director-overview.md) | Director overview for procurement, lifecycle, deployment risk, and operational readiness. |
| [`reports/project-coherent-storage_overview__engineering-overview.md`](reports/project-coherent-storage_overview__engineering-overview.md) | Engineering/ARB overview for data paths, CXL roles, namespace rules, and validation checklist. |
| [`reports/project-coherent-storage_s3-object-rest-api-translator-design.md`](reports/project-coherent-storage_s3-object-rest-api-translator-design.md) | Translator design report for S3/Object REST access and explicit prefix-cache namespace modalities. |
| [`api/coherence-ce-vllm-adapter.openapi.yaml`](api/coherence-ce-vllm-adapter.openapi.yaml) | OpenAPI contract for Coherence-CE vLLM adapter operations. |
| [`api/s3-object-rest-translator.openapi.yaml`](api/s3-object-rest-translator.openapi.yaml) | OpenAPI contract for S3/Object REST translator routes, including Unified and Dimensional Indexed Namespace routes. |
| `adr/diagrams/*.puml`, `*.png`, `*.svg` | Per-ADR PlantUML source and rendered PNG/SVG assets. |
| `diagrams/*.puml`, `*.png`, `*.svg` | Report-level PlantUML source and rendered PNG/SVG assets. |
| [`review-artifacts/rag-extraction-and-source-map.md`](review-artifacts/rag-extraction-and-source-map.md) and JSON peer | Extraction evidence and source map. |


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
| [`ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.md`](adr/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.md) | Defines the S3/Object-to-REST translator and its object, KV, vector, and prefix-cache REST contract. |
| [`ADR-023_Coherence_CE_Namespace_Modalities.md`](adr/ADR-023_Coherence_CE_Namespace_Modalities.md) | Defines Unified Namespace and Dimensional Indexed Namespace workflows, API route semantics, and locality-governance rules. |


## Top-down architecture composition

The design composes the system from inference SLOs down through hot-state placement, namespace modality, data tiers, fabrics, offload, durable media, scheduler admission, failure semantics, CXL/UA-Link pod resources, heterogeneous accelerator governance, S3/Object REST translation, and research-publication workflow. Each ADR embeds its PNG diagram and has a PlantUML source file plus PNG/SVG renders under `adr/diagrams/`.

| ADR | Architecture interaction diagram |
| --- | --- |
| [`ADR-001_Inference_Storage_Principles_and_SLOs.md`](adr/ADR-001_Inference_Storage_Principles_and_SLOs.md) | [PNG](adr/diagrams/ADR-001_Inference_Storage_Principles_and_SLOs.png) / [SVG](adr/diagrams/ADR-001_Inference_Storage_Principles_and_SLOs.svg) / [PUML](adr/diagrams/ADR-001_Inference_Storage_Principles_and_SLOs.puml) |
| [`ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md`](adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md) | [PNG](adr/diagrams/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.png) / [SVG](adr/diagrams/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.svg) / [PUML](adr/diagrams/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.puml) |
| [`ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md`](adr/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md) | [PNG](adr/diagrams/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.png) / [SVG](adr/diagrams/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.svg) / [PUML](adr/diagrams/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.puml) |
| [`ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md`](adr/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md) | [PNG](adr/diagrams/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.png) / [SVG](adr/diagrams/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.svg) / [PUML](adr/diagrams/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.puml) |
| [`ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md`](adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md) | [PNG](adr/diagrams/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.png) / [SVG](adr/diagrams/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.svg) / [PUML](adr/diagrams/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.puml) |
| [`ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md`](adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md) | [PNG](adr/diagrams/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.png) / [SVG](adr/diagrams/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.svg) / [PUML](adr/diagrams/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.puml) |
| [`ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md`](adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md) | [PNG](adr/diagrams/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.png) / [SVG](adr/diagrams/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.svg) / [PUML](adr/diagrams/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.puml) |
| [`ADR-008_RAG_Vector_Index_and_Corpus_Service.md`](adr/ADR-008_RAG_Vector_Index_and_Corpus_Service.md) | [PNG](adr/diagrams/ADR-008_RAG_Vector_Index_and_Corpus_Service.png) / [SVG](adr/diagrams/ADR-008_RAG_Vector_Index_and_Corpus_Service.svg) / [PUML](adr/diagrams/ADR-008_RAG_Vector_Index_and_Corpus_Service.puml) |
| [`ADR-009_Observability_Benchmarking_and_Rollout_Gates.md`](adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.md) | [PNG](adr/diagrams/ADR-009_Observability_Benchmarking_and_Rollout_Gates.png) / [SVG](adr/diagrams/ADR-009_Observability_Benchmarking_and_Rollout_Gates.svg) / [PUML](adr/diagrams/ADR-009_Observability_Benchmarking_and_Rollout_Gates.puml) |
| [`ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md`](adr/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md) | [PNG](adr/diagrams/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.png) / [SVG](adr/diagrams/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.svg) / [PUML](adr/diagrams/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.puml) |
| [`ADR-011_KV_Durability_Classes.md`](adr/ADR-011_KV_Durability_Classes.md) | [PNG](adr/diagrams/ADR-011_KV_Durability_Classes.png) / [SVG](adr/diagrams/ADR-011_KV_Durability_Classes.svg) / [PUML](adr/diagrams/ADR-011_KV_Durability_Classes.puml) |
| [`ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md`](adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md) | [PNG](adr/diagrams/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.png) / [SVG](adr/diagrams/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.svg) / [PUML](adr/diagrams/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.puml) |
| [`ADR-013_Failure_Semantics_and_Fencing.md`](adr/ADR-013_Failure_Semantics_and_Fencing.md) | [PNG](adr/diagrams/ADR-013_Failure_Semantics_and_Fencing.png) / [SVG](adr/diagrams/ADR-013_Failure_Semantics_and_Fencing.svg) / [PUML](adr/diagrams/ADR-013_Failure_Semantics_and_Fencing.puml) |
| [`ADR-014_Coherence_Metrics_Scheduler_Admission.md`](adr/ADR-014_Coherence_Metrics_Scheduler_Admission.md) | [PNG](adr/diagrams/ADR-014_Coherence_Metrics_Scheduler_Admission.png) / [SVG](adr/diagrams/ADR-014_Coherence_Metrics_Scheduler_Admission.svg) / [PUML](adr/diagrams/ADR-014_Coherence_Metrics_Scheduler_Admission.puml) |
| [`ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md`](adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md) | [PNG](adr/diagrams/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.png) / [SVG](adr/diagrams/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.svg) / [PUML](adr/diagrams/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.puml) |
| [`ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md`](adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md) | [PNG](adr/diagrams/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.png) / [SVG](adr/diagrams/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.svg) / [PUML](adr/diagrams/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.puml) |
| [`ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md`](adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md) | [PNG](adr/diagrams/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.png) / [SVG](adr/diagrams/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.svg) / [PUML](adr/diagrams/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.puml) |
| [`ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md`](adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md) | [PNG](adr/diagrams/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.png) / [SVG](adr/diagrams/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.svg) / [PUML](adr/diagrams/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.puml) |
| [`ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md`](adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md) | [PNG](adr/diagrams/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.png) / [SVG](adr/diagrams/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.svg) / [PUML](adr/diagrams/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.puml) |
| [`ADR-020_CXL_Memory_Pools_for_UALink_Pods.md`](adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.md) | [PNG](adr/diagrams/ADR-020_CXL_Memory_Pools_for_UALink_Pods.png) / [SVG](adr/diagrams/ADR-020_CXL_Memory_Pools_for_UALink_Pods.svg) / [PUML](adr/diagrams/ADR-020_CXL_Memory_Pools_for_UALink_Pods.puml) |
| [`ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md`](adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md) | [PNG](adr/diagrams/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.png) / [SVG](adr/diagrams/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.svg) / [PUML](adr/diagrams/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.puml) |
| [`ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.md`](adr/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.md) | [PNG](adr/diagrams/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.png) / [SVG](adr/diagrams/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.svg) / [PUML](adr/diagrams/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.puml) |
| [`ADR-023_Coherence_CE_Namespace_Modalities.md`](adr/ADR-023_Coherence_CE_Namespace_Modalities.md) | [PNG](adr/diagrams/ADR-023_Coherence_CE_Namespace_Modalities.png) / [SVG](adr/diagrams/ADR-023_Coherence_CE_Namespace_Modalities.svg) / [PUML](adr/diagrams/ADR-023_Coherence_CE_Namespace_Modalities.puml) |


## ADR diagram gallery

### [ADR-001_Inference_Storage_Principles_and_SLOs.md](adr/ADR-001_Inference_Storage_Principles_and_SLOs.md)

![ADR-001_Inference_Storage_Principles_and_SLOs](adr/diagrams/ADR-001_Inference_Storage_Principles_and_SLOs.png)

### [ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md](adr/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.md)

![ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane](adr/diagrams/ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane.png)

### [ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md](adr/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.md)

![ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers](adr/diagrams/ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers.png)

### [ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md](adr/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.md)

![ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths](adr/diagrams/ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths.png)

### [ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md](adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md)

![ADR-005_DPU_and_SmartNIC_Offload_Boundaries](adr/diagrams/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.png)

### [ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md](adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md)

![ADR-006_OpenZFS_NVMe_oF_and_Media_Layout](adr/diagrams/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.png)

### [ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md](adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md)

![ADR-007_Inference_Scheduler_Locality_and_Admission_Control](adr/diagrams/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.png)

### [ADR-008_RAG_Vector_Index_and_Corpus_Service.md](adr/ADR-008_RAG_Vector_Index_and_Corpus_Service.md)

![ADR-008_RAG_Vector_Index_and_Corpus_Service](adr/diagrams/ADR-008_RAG_Vector_Index_and_Corpus_Service.png)

### [ADR-009_Observability_Benchmarking_and_Rollout_Gates.md](adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.md)

![ADR-009_Observability_Benchmarking_and_Rollout_Gates](adr/diagrams/ADR-009_Observability_Benchmarking_and_Rollout_Gates.png)

### [ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md](adr/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.md)

![ADR-010_Coherence_CE_Write_Policy_to_OpenZFS](adr/diagrams/ADR-010_Coherence_CE_Write_Policy_to_OpenZFS.png)

### [ADR-011_KV_Durability_Classes.md](adr/ADR-011_KV_Durability_Classes.md)

![ADR-011_KV_Durability_Classes](adr/diagrams/ADR-011_KV_Durability_Classes.png)

### [ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md](adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md)

![ADR-012_Coherence_CE_vLLM_Adapter_API_Contract](adr/diagrams/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.png)

### [ADR-013_Failure_Semantics_and_Fencing.md](adr/ADR-013_Failure_Semantics_and_Fencing.md)

![ADR-013_Failure_Semantics_and_Fencing](adr/diagrams/ADR-013_Failure_Semantics_and_Fencing.png)

### [ADR-014_Coherence_Metrics_Scheduler_Admission.md](adr/ADR-014_Coherence_Metrics_Scheduler_Admission.md)

![ADR-014_Coherence_Metrics_Scheduler_Admission](adr/diagrams/ADR-014_Coherence_Metrics_Scheduler_Admission.png)

### [ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md](adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md)

![ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction](adr/diagrams/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.png)

### [ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md](adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md)

![ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails](adr/diagrams/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.png)

### [ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md](adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md)

![ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow](adr/diagrams/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.png)

### [ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md](adr/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.md)

![ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains](adr/diagrams/ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains.png)

### [ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md](adr/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.md)

![ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning](adr/diagrams/ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning.png)

### [ADR-020_CXL_Memory_Pools_for_UALink_Pods.md](adr/ADR-020_CXL_Memory_Pools_for_UALink_Pods.md)

![ADR-020_CXL_Memory_Pools_for_UALink_Pods](adr/diagrams/ADR-020_CXL_Memory_Pools_for_UALink_Pods.png)

### [ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md](adr/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.md)

![ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance](adr/diagrams/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.png)

### [ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.md](adr/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.md)

![ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator](adr/diagrams/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.png)

### [ADR-023_Coherence_CE_Namespace_Modalities.md](adr/ADR-023_Coherence_CE_Namespace_Modalities.md)

![ADR-023_Coherence_CE_Namespace_Modalities](adr/diagrams/ADR-023_Coherence_CE_Namespace_Modalities.png)


## arXiv S3 tooling

Credential-safe requester-pays S3 tools were added at:

`RAG-Scripts/arxiv-s3/`

They support manifest fetch, manifest indexing, full/targeted/monthly download planning, raw tar retention, full explosion of PDF/source tar chunks, PDF text extraction, and validation reporting. Downloading waits on AWS requester-pays credentials and AWS CLI installation.

## Public claim guardrail

UA-Link, CXL, RoCEv2, DPU, and heterogeneous GPU claims must use the evidence-grade rule:

- Direct: source explicitly states the relationship or capability.
- Adjacent: relevant to architecture but not proof of a named integration.
- Negative-control: retained to prevent overclaiming.
- Not found in current sweep: searched but no direct source-backed mention found.
