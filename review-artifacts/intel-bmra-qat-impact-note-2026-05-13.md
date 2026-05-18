# Intel BMRA and QAT Impact Note

**Generated:** 2026-05-13  
**Package:** Project Coherent Storage ADRs 2026-Q2  
**Supplemental source cache:** `processing-cache/project-coherent-rag-text-extra`

## Reviewed sources

| Source ID | File | Extracted text | Role in ADR package |
| --- | --- | ---: | --- |
| R251 | `Intel-Network-Edge-Container-Metal-Reference-Systems-Architecture-User-Guide.1706608508.pdf` | 163684 bytes | Bare-metal/container/VM deployment architecture, hardware inventory, BIOS/kernel/IOMMU/SR-IOV/hugepage setup, device-plugin deployment, telemetry stack, MinIO/operator context, QAT deployment context, and post-deployment checks. |
| R252 | `Intel-QAT-Latest-8960-C3000.pdf` | 344623 bytes | QAT Linux release notes for 1.7-generation devices including QAT Adapter 8960/8970 and Atom C3000-class hosts; crypto/compression features; Xen/SR-IOV/VF/PF support and limits; trust, reset, firmware/driver, endpoint, and virtualization caveats. |

## Architecture deltas

1. **QAT is modeled as a local trusted accelerator, not a DPU.** QAT may accelerate TLS/IPsec, crypto helper, and compression/decompression paths, but it does not own NVMe-oF offload, RDMA memory/rkey mediation, tenant fabric isolation, or OpenZFS durability evidence.
2. **BMRA-style deployment evidence becomes a rollout gate.** Hardware BOM, BIOS/UEFI state, kernel boot parameters, IOMMU/SR-IOV, hugepages, device plugins, telemetry, playbook/profile versions, and post-deployment verification outputs must be captured before lab/profile promotion.
3. **QAT virtualization is fail-closed.** VF/PF assignment is allowed only for trusted guests or trusted driver domains. Untrusted guest exposure, userspace-direct exposure to untrusted workloads, stale PF/VF ownership, endpoint errors, or ambiguous driver/firmware state produces RED/DRAIN for QAT-dependent placement.
4. **QAT fallback is explicit.** QAT endpoint, service, reset, or VF/PF failures must drain or fall back to CPU software with known SLO impact. Host QAT driver removal/reset while guest VFs are active is disallowed by operational policy.
5. **OpenZFS remains authoritative for durability.** QAT compression or cryptographic assistance never substitutes for OpenZFS checksums, synchronous write evidence, mirror state, SLOG/ZIL evidence, or Coherence-CE durability-class acknowledgements.
6. **The vLLM adapter contract remains clean.** vLLM and peer inference actors continue to talk only to Coherence-CE APIs. QAT, DPU, OpenZFS, NVMe-oF, RoCEv2, RDMA, and CXL state is summarized by owning services and scheduler-safe admission signals.

## ADR and operations files revised

| File | Change summary |
| --- | --- |
| `adr/ADR-005_DPU_and_SmartNIC_Offload_Boundaries.md` | Adds QAT-vs-DPU distinction, QAT trust/fallback rules, VF/PF/reset risks, and acceptance gates. |
| `adr/ADR-006_OpenZFS_NVMe_oF_and_Media_Layout.md` | Adds QAT compression/crypto qualification while preserving OpenZFS as durability authority. |
| `adr/ADR-007_Inference_Scheduler_Locality_and_Admission_Control.md` | Adds QAT state as service-owned scheduler input without leaking it to inference actors. |
| `adr/ADR-009_Observability_Benchmarking_and_Rollout_Gates.md` | Adds BMRA deployment evidence gates and QAT canary/telemetry requirements. |
| `adr/ADR-013_Failure_Semantics_and_Fencing.md` | Adds QAT endpoint/VF/PF/driver/service failure semantics and recovery evidence. |
| `adr/ADR-014_Coherence_Metrics_Scheduler_Admission.md` | Adds QAT metrics, freshness, reason-code, and admission behavior. |
| `operations/failure-semantics-matrix.md` | Adds QAT failure mode, recovery checklist, and drill requirement. |
| `operations/scheduler-admission-rollup.md` | Adds QAT platform summaries and reason codes. |
| `api/openai-compatible-extension-contract.md` | Extends forbidden lower-layer fields to QAT and CXL selectors so vLLM/OpenAI-compatible clients stay Coherence-only. |
| `review-artifacts/rag-manifest.*`, `review-artifacts/rag-adr-impact-ledger.md`, `review-artifacts/extraction-report.md` | Adds R251/R252 source inventory, extraction, and impact evidence. |

## Remaining qualification work

- Build host-profile evidence for each QAT-bearing host: integrated vs AIC form, device model, driver package, firmware, kernel, BIOS, IOMMU/SR-IOV state, PF/VF map, VM machine type, and telemetry endpoint.
- Define a QAT canary workload that checks crypto/compression correctness, destination-buffer guard behavior, endpoint error handling, reset/quiesce behavior, rate-limit/utilization telemetry where supported, and CPU fallback SLO.
- Ensure the scheduler reason-code vocabulary includes `qat_endpoint_degraded`, `qat_assignment_untrusted`, `qat_pf_vf_map_stale`, and `qat_fallback_active`.
- Prove that Coherence-CE/OpenAI-compatible API responses expose only Coherence policy/admission state, never QAT, OpenZFS, DPU, RoCEv2, RDMA, or CXL control knobs.
