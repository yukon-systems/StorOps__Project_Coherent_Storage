# Project Coherent Storage ADR Package v3

**Project:** Project Coherent Storage  
**Version:** 2026-Q2  
**Package revision:** v3 roadmap, rapid-awareness, CXL/DPU/AI-storage research update  
**Directory:** `RFC_Proj-Coherent-Storage-ADRs-2026-Q2.v3`  
**Generated:** 2026-05-15  
**Status:** Proposed / research-publication draft

## Purpose

This v3 package updates the Project Coherent Storage ADR set after the May 15, 2026 Marvell/XConn/CXL/DPU/RDMA/NVMe-oF/AI-storage RAG refresh. It preserves the v2 architectural baseline while adding:

1. a tiered **Rapid Awareness Training Session** report for Executive Summary, Director Review, and Technical Engineering / Architecture Review Board audiences;
2. updated ADR guidance for CXL roadmap evidence, CXL-enabled KV-cache research, DPU/protocol-offload storage paths, and public-claim guardrails;
3. PlantUML diagrams for audience tiering, data path, CXL decision flow, and arXiv/RAG metadata ingestion;
4. arXiv-ready source files in Markdown, LaTeX, and BibTeX; and
5. an explicit research-metadata workflow for arXiv API/bulk-data usage, including current API rate-limit evidence captured during this run.

The v3 package intentionally uses the user-requested hyphenated package name, while v0-v2 remain under their original dotted names.

## What changed from v2

| Area | v2 position | v3 update |
| --- | --- | --- |
| CXL role | Governed T1/T1.5 memory tier; explicit switch-fabric qualification; OpenZFS-adjacent use only by semantics | Adds roadmap/public-evidence tiers, Marvell/XConn acquisition and product-roadmap evidence, XConn CXL 3.1/PCIe 6.2 direction, and latest CXL KV-cache / CXL SSD research. |
| KV cache | vLLM and peer runtimes connect only to Coherence-CE; no OpenZFS/DPU/RDMA leakage | Adds CXL-PNM and TraCT research as **Coherence-owned implementation options**, not actor-visible API changes. |
| DPU / protocol offload | DPU/SmartNIC hardware required for storage network paths, with host fallback degraded | Adds NVIDIA BlueField/STX, Xsight/Hammerspace, Broadcom retimer, Marvell NVMe-oF, Pure/Marvell NVMe-oF/RoCE evidence as direct/adjacent/negative-control classes. |
| Public claims | v2 cited RAG sources but did not classify partnership directness in training form | v3 introduces evidence-grade guardrails: direct, adjacent, negative-control, and not-found-in-current-sweep. |
| Research publication | Markdown ADR package only | Adds arXiv-oriented `latex/project-coherent-storage-v3.tex`, `latex/references.bib`, and `latex/README-arxiv-submission.md`. |
| Metadata refresh | RAG source manifests | Adds `research/arxiv-cxl-dpu-storage-metadata-2026-05-15.*`; arXiv API attempts were rate-limited and documented. |

## Document index

| Path | Purpose |
| --- | --- |
| `reports/rapid-awareness-training-cxl-dpu-ai-storage-2026-q2-v3.md` | Main tiered report for executives, directors, and ARB/engineering. |
| `adr/ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction.md` | Revised v3 CXL/OpenZFS interaction ADR. |
| `adr/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.md` | New ADR: how to classify roadmap/partnership evidence in reports and training. |
| `adr/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.md` | New ADR: arXiv metadata/API/bulk-data and publication workflow. |
| `diagrams/*.puml` + `.png` + `.svg` | PlantUML source and rendered diagrams. |
| `latex/project-coherent-storage-v3.tex` | arXiv-oriented LaTeX manuscript. |
| `latex/references.bib` | BibTeX bibliography for the manuscript and report. |
| `research/arxiv-cxl-dpu-storage-metadata-2026-05-15.*` | API query plan/result artifact; current run encountered arXiv 429 rate limits. |

## ADR index

The package inherits ADR-001 through ADR-014 from v2 and updates/extends the CXL and publication-facing layers:

| ADR | Title | v3 disposition |
| --- | --- | --- |
| ADR-001 | Inference Storage Principles and SLOs | Inherited; v3 report reiterates TTFT/TPOT/cache locality training framing. |
| ADR-002 | Hot KV and Prefix Cache Data Plane | Inherited with v3 note: CXL KV research is hidden behind Coherence-CE. |
| ADR-003 | Model Weight, Object, and Corpus Data Tiers | Inherited. |
| ADR-004 | RDMA Fabric and GPU-Direct Data Paths | Inherited with v3 note: DPU/STX/Xsight/Broadcom are evidence-classified before claims. |
| ADR-005 | DPU and SmartNIC Offload Boundaries | Inherited; v3 report reinforces DPU hardware as required for storage-network offload. |
| ADR-006 | OpenZFS, NVMe-oF, and Media Layout | Inherited; v3 keeps OpenZFS durability below Coherence-CE. |
| ADR-007 | Inference Scheduler Locality and Admission Control | Inherited; v3 adds audience-level scheduler admission teaching path. |
| ADR-008 | RAG Vector Index and Corpus Service | Inherited. |
| ADR-009 | Observability, Benchmarking, and Rollout Gates | Inherited; v3 adds training-readiness and claim-evidence validation. |
| ADR-010 | Coherence-CE Write Policy to OpenZFS | Inherited. |
| ADR-011 | KV Durability Classes | Inherited. |
| ADR-012 | Coherence-CE vLLM Adapter API Contract | Inherited; no actor-visible CXL/DPU/OpenZFS leakage. |
| ADR-013 | Failure Semantics and Fencing | Inherited; v3 emphasizes CXL fabric manager and metadata-pipeline failure modes. |
| ADR-014 | Coherence Metrics to Scheduler Admission | Inherited. |
| ADR-015 | CXL Memory Tiering and OpenZFS Interaction | Revised for v3 research and roadmap tiers. |
| ADR-016 | Roadmap Evidence and Public Claim Guardrails | New. |
| ADR-017 | Research Metadata and arXiv Publication Workflow | New. |

## RAG evidence basis

Primary RAG addenda used by v3:

- `/home/cdex-routeros/src/RAG-DATA/ARCHIVE-ADD-Marvell-XConn-CXL-DPU-RDMA-NVMeoF-2026-05-15.json`
- `/home/cdex-routeros/src/RAG-DATA/ARCHIVE-ADD-Strategic-Partnerships-CXL-AI-Storage-2026-05-15.json`
- `/home/cdex-routeros/src/RAG-DATA/ARCHIVE-ADD-V3-Arxiv-CXL-KV-Storage-Latest-2026-05-15.json`
- `/home/cdex-routeros/src/RAG-DATA/STRATEGIC-PARTNERSHIP-EVIDENCE-MATRIX-CXL-AI-STORAGE-2026-05-15.md`

Important guardrail: v3 distinguishes direct Marvell/XConn CXL evidence from adjacent NVIDIA BlueField/STX, Xsight, Broadcom, Pure Storage, Dell/HPE, IBM, Oracle/OCI, and OpenZFS evidence. Adjacent evidence may inform architecture, but must not be promoted to a direct partnership/integration claim without a direct source.

## arXiv readiness boundary

The LaTeX/BibTeX files are source-ready drafts, not a completed arXiv submission. This host has `bibtex` and `plantuml`, but no `pdflatex`, `latexmk`, or `tectonic`; PDF compilation was therefore not performed locally. The package includes an arXiv submission checklist and keeps diagrams as PNG/SVG plus PlantUML source.
