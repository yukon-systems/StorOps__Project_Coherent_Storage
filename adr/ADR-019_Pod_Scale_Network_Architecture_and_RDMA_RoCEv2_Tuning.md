# ADR-019: Pod-Scale Network Architecture and RDMA/RoCEv2 Tuning

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Status:** Proposed  
**Generated:** 2026-05-17

## Decision summary

Define pod networking as multiple governed planes: UA-Link scale-up, RoCEv2/RDMA scale-out, DPU-mediated storage/NVMe-oF, frontend/API, management, and timing. RoCEv2 performance tuning is mandatory architecture work, not a post-deployment switch knob.

## Decision

- Separate traffic into classes: frontend/API, inference control, KV hydration, collectives, storage/NVMe-oF, CXL/pool management, scrub/resilver/rebuild, management, and timing.
- Use PFC only for lossless classes that require it; do not globally enable PFC across all traffic.
- Use ECN/DCQCN or device-equivalent congestion-control settings validated for each link speed, buffer profile, and workload.
- Use consistent MTU, DSCP/PCP, queue mapping, ECN marking, CNP handling, and pause configuration across hosts, DPUs, NICs, switches, and overlays.
- Use rail-aware placement for GPU/NIC affinity and dual-plane designs where failure-domain or bisection requirements justify them.
- Evaluate OCP MRC and packet-spraying approaches as future multipath/RDMA options, not as immediate assumptions.
- Gate scheduler admission on fabric telemetry freshness and tail-latency evidence.

## Initial tuning parameters to capture

| Category | Required capture |
| --- | --- |
| Link/MTU | link speed, width, FEC, MTU, VLAN/VRF/overlay MTU, headroom. |
| QoS | traffic class, DSCP/PCP, queue, scheduler, PFC enablement, pause threshold. |
| ECN/DCQCN | ECN min/max thresholds, CNP handling, rate-increase/decrease profile, RTT. |
| RDMA | QP limits, MR/cache pressure, completion queue sizing, inline threshold, retry counters. |
| DPU/NIC | firmware, offload mode, memory registration, telemetry endpoint, isolation policy. |
| Telemetry | pause duration, ECN marks, CNP rate, drops, trims, retransmits, RTT, p99/p999 latency. |

## Acceptance criteria

- No pod is promoted without a recorded RoCEv2 QoS profile and rollback profile.
- Storage/NVMe-oF traffic has separate class/plane or admission limits from accelerator collectives.
- Telemetry stale state maps to AMBER/RED/DRAIN.
- Failure drills cover PFC storm, ECN mis-threshold, link downshift, rail failure, DPU failover, and storage rebuild congestion.

## Source documents

- S04/S05: OCP inference/training fabric RAs.
- S06: OCP MRC.
- S07/S08/S09: lossless Ethernet, Arista/Broadcom RoCE deployment guidance.
- S10/S11/S12: AMD Pensando/Pollara cluster and product collateral.
