# Project Coherent Storage Overview: Engineering Overview

**Project:** Project Coherent Storage
**Audience:** Technical engineering / architecture review board
**Architecture cycle:** 2026-Q2
**Generated:** 2026-05-18
**Status:** Proposed training/report draft

## Architecture assertion

All KV-cache and prefix-cache traffic enters Coherence-CE. Coherence-CE may choose GPU HBM, host DRAM, CXL T1/T1.5, OpenZFS-backed write policy, RDMA object paths, or NVMe-oF-backed durable storage according to KV durability class, namespace modality, and admission state. vLLM, OpenAI-compatible adapters, and peer inference actors must not depend on lower-layer implementation details.

## Data path summary

1. **Inference actor path:** OpenAI-compatible client or vLLM adapter -> Coherence-CE API -> Coherence-CE Memory Mesh.
2. **Hot state path:** Coherence-CE -> GPU HBM/local DRAM for KV-D0/D1 active decode.
3. **Warm state path:** Coherence-CE -> host DRAM/CXL T1.5 for recomputable or warm KV/prefix staging if latency qualifies.
4. **Durable state path:** Coherence-CE write policy -> DPU-mediated NVMe-oF/RDMA -> OpenZFS mirrored NAND.
5. **Namespace path:** Unified Namespace for simple global identity; Dimensional Indexed Namespace for region/datacenter/pod/locality-epoch scoped authority.
6. **Scheduler path:** Coherence-CE metrics -> rollup -> admission state GREEN/AMBER/RED/DRAIN.

## CXL role classification

| CXL role | Allowed role | Required evidence |
| --- | --- | --- |
| Direct-attached volatile Type-3 memory | Warm Coherence metadata, KV-D1/D2 staging, vector heads, ARC-like capacity with budgets. | NUMA locality, p99 latency, bandwidth, thermal and error telemetry. |
| CXL pooled memory | T1.5 warm/shared memory for recomputable state. | Fabric manager, pool ownership epoch, link state, failover and fencing drills. |
| CXL PNM / near-memory compute | Research-qualified option for KV/filter/compression work. | API isolation behind Coherence-CE, benchmark proof, security boundary review. |
| CXL block-presented persistent media | Candidate L2ARC/SLOG/special vdev only after explicit media qualification. | Power-loss protection, flush semantics, endurance, mirroring, import/replacement drills. |
| Hidden switched/bifurcated CXL | Rejected for production-like latency/durability paths. | Use only for lab discovery if topology is visible and measured. |

## Namespace engineering rules

- Exact prefix-cache put/get/delete operations require `prefix_id`.
- Search and invalidate are collection operations with explicit bodies.
- Unified Namespace hides locality and routing inside Coherence-CE.
- Dimensional Indexed Namespace requires `index_id` and declared dimensions for locality-aware authority.
- `index_id` is not a physical identifier. It must not encode zpool names, NVMe namespaces, DPU queue pairs, RDMA QP/rkey values, VLAN IDs, CXL device names, or storage-node hostnames.
- Scheduler metrics must be rollable by `namespace_mode`, `namespace`, `index_id`, `tenant_id`, `model_id`, `durability_class`, and `locality_epoch`.

## ARB review checklist

- [ ] Does every CXL device have a role: volatile memory, pooled memory, persistent memory, block media, or rejected?
- [ ] Is CXL topology recorded by socket, root complex, link width/speed, switch hop count, NUMA node, and firmware?
- [ ] Are vLLM adapters isolated from OpenZFS/DPU/CXL/RDMA implementation details?
- [ ] Are DPU storage paths required and telemetry-fed into scheduler admission?
- [ ] Are prefix-cache exact routes ID scoped in OpenAPI and documentation?
- [ ] Are Unified Namespace and Dimensional Indexed Namespace workflows both documented and tested?
- [ ] Are claims about partnerships classified as direct/adjacent/negative-control/not-found?
- [ ] Are arXiv/RAG metadata refreshes reproducible and citation-backed?

## Recommended training agenda

| Time | Segment | Audience |
| --- | --- | --- |
| 10 min | Why inference storage differs from generic HPC storage | All |
| 10 min | Coherence-CE, DPU, OpenZFS, CXL, and namespace boundaries | Engineering / ARB |
| 15 min | API contracts and prefix-cache route generation | Engineering / ARB |
| 20 min | Technical data path and failure semantics | Engineering / ARB |
| 20 min | CXL decision tree and topology traps | Director / ARB |
| 15 min | Scheduler admission and observability | Director / ARB |
| 10 min | arXiv/RAG metadata refresh workflow | Research / ARB |

## Source anchors

This overview is derived from the ADR package, `review-artifacts/rag-extraction-and-source-map.md`, `latex/references.bib`, and the architecture reports in `reports/`.
