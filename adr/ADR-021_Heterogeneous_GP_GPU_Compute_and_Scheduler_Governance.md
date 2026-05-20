# ADR-021: Heterogeneous GP-GPU Compute and Scheduler Governance

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Status:** Proposed  
**Generated:** 2026-05-17

## Architecture diagram

![ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance](diagrams/ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance.png)

## Decision summary

Admit heterogeneous general-purpose GPU and accelerator resources through capability profiles. The scheduler must reason about GPU vendor/runtime, HBM capacity, collective library, RDMA memory semantics, UA-Link or vendor scale-up topology, CXL pool locality, DPU/NIC proximity, power/cooling headroom, and failure domain.

## Decision

- Define accelerator profiles for NVIDIA, AMD, Intel, DPU/IPU, FPGA/NPU, and edge accelerators.
- Require each profile to declare supported precision, compiler/runtime, collective backend, direct-memory/RDMA semantics, memory capacity, fabric locality, telemetry, and isolation model.
- Use cross-vendor collective research as an enablement path, not as default production behavior.
- Avoid mixing GPU classes in one latency-critical inference scope unless the model execution plan and collectives are qualified.
- Admit heterogeneous resources first for batch, evaluation, embedding, preprocessing, or fault-tolerant inference classes before critical TTFT/TPOT paths.

## Cross-platform accelerator call-outs

Scheduler governance must separate **portable feature validation** from **backend-specific accelerator qualification**:

- The user-visible inference contract is validated through OpenAI-compatible or Coherence-native APIs exposed by model-serving and cache services such as vLLM, SGLang, Triton, Ollama, LocalAI, LM Studio/LM Link, or site-equivalent adapters.
- CUDA, TensorRT, ROCm, oneAPI/SYCL, OpenVINO, vendor NPU SDKs, and collective backends such as NCCL, RCCL, oneCCL, or HetCCL are backend qualification paths, not actor-visible API requirements.
- Linux is the expected qualification platform for CUDA/NVIDIA and many RDMA/GPU-direct backend profiles. FreeBSD, Solaris, and illumos service roles remain valid where they provide NFS, ZFS, proxy, firewall, observability, object, or API roles without that accelerator backend.
- A platform that lacks a backend must report `SKIPPED_PLATFORM` or `INCONCLUSIVE_BACKEND`, not a failed architecture feature, when the portable service contract can still be validated through CPU, ONNX Runtime, SYCL/oneAPI where available, or service-level HTTP tests.
- Benchmark and E2ET evidence for accelerator features must name both the portable feature result and the backend-specific result so scheduler admission can distinguish "feature works" from "this vendor/runtime/device path is qualified."

## Acceptance criteria

- Scheduler profiles include vendor/runtime, memory, direct RDMA capability, collectives, CXL reachability, DPU/NIC affinity, and UA-Link/domain membership.
- Mixed-vendor runs have explicit straggler detection, fallback, and rollback.
- Power/cooling/timing telemetry participates in admission for dense pods.
- Coherence-CE metrics remain model/tenant/class scoped and do not leak hardware internals to actor APIs.
- Cross-platform accelerator results distinguish portable service validation from backend-specific qualification or platform skip states.

## Source documents

- S13: Intel Gaudi 3 cluster reference design.
- S14: HetCCL heterogeneous GPU collectives research.
- S10/S11/S12: AMD Instinct/Pensando/Pollara evidence.
- S03: intra-node communication bottleneck analysis.
