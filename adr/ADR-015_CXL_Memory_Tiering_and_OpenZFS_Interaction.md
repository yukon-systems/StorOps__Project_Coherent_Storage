# ADR-015: CXL Memory Tiering and OpenZFS Interaction

**Project:** Project Coherent Storage  
**Version:** 2026-Q2.v3  
**Status:** Proposed  
**Generated:** 2026-05-15

## Decision summary

CXL is a governed T1/T1.5 memory tier and roadmap-managed hardware option for Project Coherent Storage. It may support Coherence-CE metadata, warm KV/prefix staging, vector-index heads, write buffers, ARC-like memory pressure relief, and future CXL-PNM/CXL-SSD experiments. It is not a replacement for GPU HBM, local DDR DRAM, OpenZFS durable NAND, DPU-mediated NVMe-oF/RDMA storage paths, or Coherence-CE actor isolation.

## v3 decision

- Keep vLLM and peer inference actors isolated from CXL, OpenZFS, DPU, RoCEv2, and NVMe-oF details.
- Treat Marvell Structera, Marvell/XConn acquisition, XConn Apollo/Apollo 2, XConn/ScaleFlux, XConn/MemVerge, and CXL 3.1/4.0 materials as direct roadmap evidence for CXL memory expansion, switching, pooling, and interoperability direction.
- Treat NVIDIA BlueField/STX, Xsight/Hammerspace, Broadcom retimers, Pure/Marvell NVMe-oF/RoCE, Dell/HPE/OEM pages, IBM POWER/z references, Oracle/OCI, and OpenZFS source archives as direct only for what they explicitly say and otherwise as adjacent or negative-control evidence.
- Admit CXL first as T1.5 warm/shared capacity, not as KV-D0 active decode memory, OpenZFS sync media, or durable-class evidence.
- Allow CXL-PNM, CXL shared-memory KV, CXL SSD, and near-data-processing research only as Coherence-owned implementation experiments until local SLO and failure evidence passes.
- Require scheduler admission to track DRAM pressure, CXL pressure, CXL bandwidth, p99/p999 latency, NUMA distance, topology penalty, fabric-manager health, pool ownership epoch, thermal state, and error counters.
- For OpenZFS, use CXL only through semantics-qualified roles: volatile memory for ARC-like/cache/metadata budgets; persistent byte-addressable memory for PMem-aware services above OpenZFS; block-presented power-loss-protected devices for L2ARC/SLOG/special-vdev/pool roles only after media qualification.

## CXL decision tree

| Question | Decision | Consequence |
| --- | --- | --- |
| Is the state active per-token decode or GPU-local? | Use GPU HBM/local DRAM first. | CXL is not the primary hot path. |
| Is the state warm, reusable, metadata-heavy, or recomputable? | Candidate CXL T1/T1.5. | Bind to Coherence-CE placement policy. |
| Is persistence required for correctness? | Use OpenZFS-backed or qualified persistent/block media. | Volatile CXL cannot ack durability. |
| Is CXL directly attached to the correct root complex/NUMA locality? | Candidate placement. | Otherwise reject for latency-sensitive use. |
| Is CXL behind explicit managed switching? | Candidate for pooled warm memory. | Require fabric manager, ownership epoch, hop-count, RAS, and telemetry. |
| Is CXL behind hidden bifurcation or unreported switching? | Reject production-like use. | Lab discovery only. |
| Does the device expose telemetry and fault state? | Candidate rollout. | Missing telemetry maps to AMBER/RED. |

## Role matrix

| Role | Allowed | Forbidden |
| --- | --- | --- |
| Volatile CXL Type-3 memory | Coherence metadata, KV-D1/D2 staging, vector heads, read-mostly metadata, ARC-like capacity under budgets | Durable ack, SLOG, special vdev, pool media |
| CXL pooled memory | T1.5 warm/shared memory with ownership/fencing and failure drills | KV-D0 active decode, unqualified shared durable classes |
| CXL-PNM / CXL-NDP | Compression, filtering, warm KV handling, research path behind Coherence-CE | Actor-visible API dependency, tenant boundary bypass |
| CXL block-presented media | L2ARC/SLOG/special vdev only after power-loss/endurance/flush/fencing proof | Single unmirrored metadata/log device or implicit durability |
| Incidental switching/bifurcation | Lab topology mapping | Production latency or durable path |

## CXL vs Optane PMem update

CXL remains preferred for heterogeneous future deployments because it is not tied to Intel-only PMem DIMM generations and can appear through PCIe AIC, U.3-like, and EDSFF packaging. Optane PMem 200/300-class devices remain useful historical comparison points for byte-addressable persistence and memory-tier operation, but their platform coupling and lifecycle limitations make them a narrower architecture basis. CXL’s packaging flexibility increases its value and its risk: slot placement, switch depth, bifurcation, NUMA distance, firmware, and telemetry must be governed as architecture inputs, not implementation afterthoughts.

## Acceptance criteria

- Every CXL device or pool has a declared role and evidence class.
- CXL topology is captured in hardware source-of-truth: socket, root complex, link width/speed, switch hop count, bifurcation, firmware, NUMA node, thermal state, and telemetry endpoint.
- No actor-facing API requires CXL/OpenZFS/DPU/RDMA identifiers.
- No volatile CXL device participates in durable acknowledgements.
- OpenZFS CXL roles are admitted only by device semantics and local failure-drill proof.
- Scheduler dashboards expose CXL state separately from DRAM, OpenZFS, and DPU state.

## Source documents

- Marvell Structera CXL product and switch materials.
- Marvell acquisition/completion of XConn.
- XConn Apollo/Apollo 2, ScaleFlux, AMD, MemVerge, Liqid, and OCP ecosystem materials.
- CXL 3.1 and CXL 4.0 support statements.
- Linux CXL driver, `ndctl`/`libcxl`, cxl-reskit, and SMDK sources.
- CXL KV-cache, CXL shared-memory KV, CXL SSD, CXL-NDP, ByteFS, and CXL database research papers in the RAG corpus.
