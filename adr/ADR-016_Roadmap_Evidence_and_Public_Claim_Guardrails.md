# ADR-016: Roadmap Evidence and Public Claim Guardrails

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Status:** Proposed  
**Generated:** 2026-05-15

## Architecture diagram

![ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails](diagrams/ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails.png)

## Decision summary

Architecture reports, training decks, and arXiv-oriented papers must classify vendor, product-roadmap, partnership, and integration evidence before using it as a claim. The allowed grades are **direct**, **adjacent**, **negative-control**, and **not-found-in-current-sweep**.

## Context

The research sweep found strong direct evidence for Marvell/XConn/CXL direction and strong adjacent evidence for AI-storage accelerator ecosystems. Without claim grading, it is easy to conflate NVIDIA BlueField/STX storage ecosystem evidence with Marvell/XConn CXL integration, or to treat OpenZFS source retention as proof of a CXL/OpenZFS integration.

## Decision

- Use direct evidence only when a source explicitly states the relationship, product capability, or integration.
- Use adjacent evidence to inform architecture options, but not to claim named-vendor integration.
- Retain negative-control sources to prevent future overclaiming.
- Use not-found-in-current-sweep language when a target relationship was searched but not found.
- Public materials must include the evidence grade in report tables when discussing vendor partnerships or product-roadmap claims.

## Evidence-grade examples

| Topic | Grade | Report-safe language |
| --- | --- | --- |
| Marvell Structera CXL and XConn acquisition | Direct | “Marvell/XConn public materials support CXL memory expansion, switching, and pooling roadmap analysis.” |
| XConn/Liqid, XConn/MemVerge, XConn/ScaleFlux, XConn/AMD | Direct | “XConn ecosystem materials support composable-memory and CXL interoperability analysis.” |
| NVIDIA BlueField/STX + VAST/Pure/NetApp/Dell/HPE/IBM/OCI | Adjacent / negative-control for Marvell/XConn | “Relevant AI-storage accelerator ecosystem; not proof of Marvell/XConn+CXL integration.” |
| Pure Storage + Marvell NVMe-oF/RoCE | Direct for historical NVMe-oF/RoCE; not CXL | “Historical protocol-offload ecosystem evidence.” |
| Broadcom CXL/PCIe retimers | Direct for Broadcom hardware; adjacent for architecture | “Useful for CXL/PCIe signal path planning; not a Marvell/XConn partnership.” |
| OpenZFS source archive | Direct for OpenZFS source; not CXL integration | “Retained for future integration analysis; no direct CXL/OpenZFS claim.” |
| Oracle/OCI + Marvell | Direct for old key-management/security collaboration; not CXL | “OCI/security reference only; not CXL AI-storage evidence.” |

## Acceptance criteria

- Every roadmap table in reports includes an evidence-grade column or explicit guardrail text.
- No public claim says “partnership,” “integration,” or “support” unless the cited source states it directly.
- Adjacent sources may be used for risk, opportunity, or comparison language only.
- Negative-control sources remain in the RAG corpus with explanation.
