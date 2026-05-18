# ADR-018: UA-Link Pod-Scale Fabric and Compute Domains

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Status:** Proposed  
**Generated:** 2026-05-17

## Decision summary

Adopt UA-Link as a governed candidate for pod/rack-scale accelerator scale-up domains. UA-Link is a lower-layer accelerator fabric and must remain hidden behind Coherence-CE and scheduler policy. It does not replace RoCEv2/RDMA scale-out, DPU-mediated NVMe-oF storage, OpenZFS durability, or the Coherence-CE API contract.

## Decision

- Model each UA-Link fabric as a **pod scale-up domain** with explicit membership, switch topology, link state, and failure boundary.
- Use UA-Link locality as a scheduler input for accelerator placement, collective-heavy inference/training, model-parallel execution, and warm KV locality.
- Keep cross-pod, storage, and control traffic on Ethernet/RDMA/storage fabrics.
- Require telemetry for link state, switch state, endpoint health, reachability, bandwidth, latency, retry/error state, and management API freshness.
- Treat UA-Link pod state as GREEN/AMBER/RED/DRAIN for scheduler admission.
- Do not expose UA-Link identifiers in vLLM/OpenAI-compatible APIs.

## Rationale

The UA-Link white paper and UniFabriX material describe an open scale-up interconnect for AI accelerators inside computing pods, with Ethernet/PCIe ecosystem leverage and pod-scale accelerator counts. Project Coherent Storage benefits from this as a locality and scale-up fabric abstraction, but the durable storage and cross-pod data plane still require Ethernet/RDMA and DPU-mediated storage paths.

## Acceptance criteria

- Every UA-Link domain has a source-of-truth record: pod ID, OS domain/system node, accelerators, switches, link width/speed, firmware, management endpoint, and failure-domain owner.
- Scheduler admission consumes UA-Link locality and health.
- Coherence-CE can prefer same-domain warm KV/prefix placement without exposing UA-Link to actors.
- Failure drills cover switch loss, endpoint loss, link downshift, partition, stale telemetry, and pod drain.

## Source documents

- S01: UA-Link white paper.
- S02: UniFabriX UA-Link material.
- S03: Intra-node communication analysis.
- S04/S05: OCP inference/training fabric scale models.
