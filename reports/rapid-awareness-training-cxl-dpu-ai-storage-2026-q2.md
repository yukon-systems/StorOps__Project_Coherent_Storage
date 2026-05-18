# Rapid Awareness Training: CXL, DPU Offload, and AI/HPC Storage for Project Coherent Storage

**Audience tiers:** Executive Summary, Director Review, Technical Engineering / Architecture Review Board  
**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Generated:** 2026-05-15  
**Status:** Proposed training/report draft

## Executive premise

Project Coherent Storage is an inference-first storage architecture. vLLM and other inference actors do not bind to OpenZFS, DPU, NVMe-oF, RoCEv2, or CXL directly. They bind to the Coherence-CE Memory Mesh, which owns KV/prefix-cache placement, durability classes, object/API translation, and scheduler-visible metrics. Beneath Coherence-CE, OpenZFS nodes provide the durable NAND block substrate; DPUs/SmartNICs mediate NVMe-oF/RDMA/storage-network offload; and CXL may provide governed memory expansion, warm KV/prefix staging, metadata memory, and future pooled-memory roles when topology and telemetry qualify.

The research update adds roadmap and ecosystem evidence for CXL and adjacent AI-storage acceleration. The strongest direct evidence is Marvell Structera CXL, Marvell/XConn CXL switching, XConn CXL 2.0/3.1 ecosystem activity, CXL standards progression, Linux CXL tooling, and CXL KV-cache / CXL SSD research. NVIDIA BlueField/STX, Xsight/Hammerspace, Broadcom retimers, Pure Storage NVMe-oF/RoCE, IBM POWER/z, Oracle/OCI, and OpenZFS source snapshots are valuable, but must be classified as direct, adjacent, negative-control, or not-found-in-current-sweep before inclusion in public claims.

## Tier 1: Executive Summary

### What leaders should remember

1. **CXL is about the memory wall, not simply more storage.** It gives the architecture a path to memory expansion and pooling for warm inference state, but it does not replace GPU HBM, local DRAM, OpenZFS durable storage, or DPU offload.
2. **DPUs remain a hard storage-network requirement.** NVMe-oF/RDMA offload, tenant boundary enforcement, telemetry, memory registration pressure, and storage-path isolation require DPU/SmartNIC hardware in the Project Coherent Storage design.
3. **Coherence-CE is the API and policy boundary.** Inference actors see Coherence-CE semantics, not CXL/OpenZFS/RDMA/DPU internals.
4. **Roadmap evidence must be graded.** Marvell/XConn CXL evidence is direct for the CXL switching/memory direction; NVIDIA BlueField/STX storage evidence is an adjacent accelerator-storage ecosystem, not proof of Marvell/XConn + BlueField + CXL integration.
5. **The business value is lower overprovisioning and better accelerator utilization.** CXL and Coherence-CE can reduce repeated KV/object hydration and relieve memory pressure, but only if tail latency and failure behavior stay inside SLO.

### Executive decision points

| Decision | Recommended posture | Rationale |
| --- | --- | --- |
| Include CXL in reports? | Yes, as a governed memory tier and roadmap option. | Direct Marvell/XConn/CXL standards and research evidence exist. |
| Claim CXL is production hot path? | No. | KV-D0 active decode must remain GPU HBM/local DRAM-first unless local evidence proves otherwise. |
| Require DPUs? | Yes. | Storage-network offload and RDMA/NVMe-oF mediation are core requirements, not optional accelerators. |
| Publish externally? | Yes, with evidence-grade language. | Public documents must separate direct evidence from adjacent ecosystem evidence. |
| Invest in lab validation? | Yes. | Vendor roadmaps do not substitute for p99 latency, bandwidth, RAS, and failure-drill evidence. |

## Tier 2: Director Review

### Operating model

Director-level review should focus on choices that change procurement, deployment, lifecycle, risk, and staffing:

- CPU platform and firmware support for CXL 2.0/3.0/3.1 and later.
- Slot/root-complex placement for CXL memory, GPU, DPU, NIC, and NVMe devices.
- DPU/SmartNIC qualification for NVMe-oF, RDMA, tenant isolation, telemetry, and fallback.
- OpenZFS node layout: mirrored NAND block tier, special vdev/SLOG/L2ARC qualification, scrub/resilver impact.
- Coherence-CE metrics integration with scheduler admission.
- Evidence-grade public communication.

### Procurement matrix

| Component | Required evidence before purchase | Governance note |
| --- | --- | --- |
| CXL memory expansion | CPU/root-complex support, BIOS/firmware, Linux CXL driver support, NUMA topology, telemetry endpoint | Do not buy capacity without lane/topology placement evidence. |
| CXL switch/fabric | Switch generation, hop count, CFM/fabric manager, pool ownership epoch, p99 latency, RAS counters | Treat as T1.5 warm/shared memory first, not active decode or durability. |
| DPU/SmartNIC | NVMe-oF/RDMA offload, memory-registration handling, tenant isolation, telemetry, host fallback | Required for storage network paths. |
| NVMe media | Endurance, flush semantics, power-loss protection, mirrored vdev plan, rebuild behavior | OpenZFS durability depends on media semantics, not roadmap claims. |
| Retimers/switches | PCIe/CXL generation, signal integrity, error telemetry, topology visibility | Avoid hidden switch/bifurcation for latency-sensitive paths. |

### Roadmap report inclusions

Use these as report-ready roadmap categories:

1. **Marvell Structera CXL line:** Structera A/X memory expansion/near-memory acceleration; Structera S switch/pooling direction.
2. **XConn CXL switching:** Apollo CXL 2.0 and Apollo 2 CXL 3.1/PCIe Gen6.2 direction; Marvell acquisition consolidates this path.
3. **CXL standards:** CXL 3.1 and CXL 4.0 support statements; OCP CMS/CFM material for composable memory management.
4. **Linux readiness:** kernel CXL docs, `cxl-cli`, `libcxl`, `ndctl`, SMDK, cxl-reskit.
5. **AI-storage acceleration:** NVIDIA BlueField/STX, Xsight/Hammerspace, Broadcom retimers, Pure/Marvell NVMe-oF/RoCE as adjacent ecosystem inputs.
6. **Research frontier:** CXL KV cache, CXL SSD, CXL-GPU, CXL-NDP, CXL database engines, CXL pooled memory, semantic eviction.

## Tier 3: Technical Engineering / Architecture Review Board

### Architecture assertion

All KV-cache traffic enters Coherence-CE. Coherence-CE may choose GPU HBM, host DRAM, CXL T1/T1.5, OpenZFS-backed write policy, RDMA object path, or NVMe-oF-backed durable storage according to KV durability class and admission state. vLLM, OpenAI-compatible adapters, and peer inference actors must not depend on the lower-layer implementation.

### Data path summary

1. **Inference actor path:** vLLM/OpenAI-compatible client → Coherence-CE adapter/API → Coherence-CE memory mesh.
2. **Hot state path:** Coherence-CE → GPU HBM/local DRAM for KV-D0/D1 active decode.
3. **Warm state path:** Coherence-CE → host DRAM/CXL T1.5 for recomputable or warm KV/prefix staging if latency qualifies.
4. **Durable state path:** Coherence-CE write policy → OpenZFS/NVMe-oF mirrored NAND via DPU-mediated storage network.
5. **Scheduler path:** Coherence-CE metrics → rollup → admission state GREEN/AMBER/RED/DRAIN.

### CXL role classification

| CXL role | Allowed role | Required evidence |
| --- | --- | --- |
| Direct-attached volatile Type-3 memory | Warm Coherence metadata, KV-D1/D2 staging, vector heads, ARC-like capacity with budgets | NUMA locality, p99 latency, bandwidth, thermal and error telemetry. |
| CXL pooled memory | T1.5 warm/shared memory for recomputable state | Fabric manager, pool ownership epoch, link state, failover and fencing drills. |
| CXL PNM / near-memory compute | Research-qualified option for KV/filter/compression work | API isolation behind Coherence-CE, benchmark proof, security boundary review. |
| CXL block-presented persistent media | Candidate L2ARC/SLOG/special vdev only after explicit media qualification | Power-loss protection, flush semantics, endurance, mirroring, import/replacement drills. |
| Hidden switched/bifurcated CXL | Rejected for production-like latency/durability paths | Use only for lab discovery if topology is visible and measured. |

### Latest research implications

- **CXL-PNM for 1M-token LLM inference**: Supports the idea that CXL can relieve GPU KV pressure, but Project Coherent Storage must keep this behind Coherence-CE and scheduler policy.
- **TraCT rack-scale CXL shared KV cache**: Supports CXL shared-memory KV transfer as a research direction for disaggregated serving, but does not replace RDMA/DPU storage-network requirements.
- **CXL SSD / WIO research**: Suggests future block-to-byte and upload-enabled computational storage paths, but OpenZFS durable-media semantics still require local qualification.
- **CXL-NDP / ByteFS / ScaleEvict**: Supports CXL as a cache/near-data-processing tier, not a universal hot-path substitute.

### ARB review checklist

- Does every CXL device have a role: volatile memory, pooled memory, persistent memory, block media, or rejected?
- Is CXL topology recorded by socket, root complex, link width/speed, switch hop count, NUMA node, and firmware?
- Are vLLM adapters isolated from OpenZFS/DPU/CXL/RDMA implementation details?
- Are DPU storage paths required and telemetry-fed into scheduler admission?
- Are claims about partnerships classified as direct/adjacent/negative-control/not-found?
- Are arXiv/RAG metadata refreshes reproducible and citation-backed?

## Public-claim evidence grading

| Claim class | Definition | Report language |
| --- | --- | --- |
| Direct | Source explicitly states the relationship/integration. | “Source X states Y.” |
| Adjacent | Source is relevant to the same architecture path but does not prove the named integration. | “Relevant adjacent ecosystem evidence.” |
| Negative-control | Source is retained to prevent accidental conflation. | “Do not treat as proof of Marvell/XConn integration.” |
| Not found in current sweep | Current sweep found no direct source. | “No direct source-backed mention found in this sweep.” |

## Recommended training agenda

| Time | Segment | Audience |
| --- | --- | --- |
| 10 min | Why inference storage differs from generic HPC storage | All |
| 10 min | Executive roadmap: CXL, DPU, Coherence-CE, OpenZFS | Executive / Director |
| 15 min | Evidence-grade vendor map and public-claim guardrails | Executive / Director / ARB |
| 20 min | Technical data path and failure semantics | ARB / Engineering |
| 20 min | CXL decision tree and topology traps | Director / ARB |
| 15 min | Scheduler admission and observability | Director / ARB |
| 10 min | arXiv/RAG metadata refresh workflow | Research / ARB |

## Source anchors

This report is derived from the package RAG manifests and the arXiv addendum. See `README.md`, `latex/references.bib`, and `research/arxiv-cxl-dpu-storage-metadata-2026-05-15.md`.
