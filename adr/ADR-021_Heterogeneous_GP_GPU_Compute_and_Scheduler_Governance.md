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

## Acceptance criteria

- Scheduler profiles include vendor/runtime, memory, direct RDMA capability, collectives, CXL reachability, DPU/NIC affinity, and UA-Link/domain membership.
- Mixed-vendor runs have explicit straggler detection, fallback, and rollback.
- Power/cooling/timing telemetry participates in admission for dense pods.
- Coherence-CE metrics remain model/tenant/class scoped and do not leak hardware internals to actor APIs.

## Source documents

- S13: Intel Gaudi 3 cluster reference design.
- S14: HetCCL heterogeneous GPU collectives research.
- S10/S11/S12: AMD Instinct/Pensando/Pollara evidence.
- S03: intra-node communication bottleneck analysis.
