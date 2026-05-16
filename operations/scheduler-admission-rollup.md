# Scheduler Admission Rollup

**Project:** Project Coherent Storage  
**Version:** 2026-Q2  
**Package:** v2 inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Purpose

This document defines how Coherence-CE metrics are rolled up into scheduler admission states. The scheduler uses this summary before admitting inference work and records the consumed summary epoch in every decision log.

## Rollup pipeline

```text
vLLM / peer runtime traces
  -> Coherence-CE lookup/publish/mesh/write-back metrics
  -> Coherence-CE durability and locality rollup
  -> platform summaries for storage, offload, QAT accelerator, CXL tier/topology, fabric, power, timing, telemetry freshness
  -> /v1/coherence/admission/summary
  -> global scheduler admission and placement decision
```

Only the Coherence/scheduler summary is an admission contract. Lower-layer metrics are diagnostic and owned by their services.

## Admission state model

| State | Entry condition | Allowed scheduler action |
| --- | --- | --- |
| GREEN | Coherence mesh, locality, write policy, durable backing, and freshness satisfy class policy | Admit and score normally |
| AMBER | Safe but degraded, near threshold, or class-limited | Admit lower-risk classes; throttle, queue, or recompute higher-risk paths |
| RED | Correctness, durability, quorum, SLO, or freshness evidence is insufficient | Reject, queue, or force recompute by class |
| DRAIN | Operator or automated drain in progress | Stop new placement; preserve/complete safe in-flight work |

## Required summary dimensions

Every summary entry must include:

- tenant/project;
- model ID;
- tokenizer/adapter/runtime profile when relevant;
- durability class;
- locality scope: node, rack, fabric plane, or cluster;
- hardware locality when relevant: CPU socket, root complex, NUMA node, QAT PF/VF profile, and CXL tier/topology profile;
- prefix shard or sampled prefix bucket;
- admission state and recommended action;
- reason codes;
- owning subsystem;
- source freshness;
- summary epoch and generation time.

## Reason codes

| Code | Owning subsystem | Typical action |
| --- | --- | --- |
| `coherence_lookup_p99_high` | coherence | Prefer local, throttle, or queue. |
| `prefix_hit_rate_low` | coherence/scheduler | Lower locality score; prewarm if budget exists. |
| `writeback_lag_high` | coherence | Throttle KV-D2 publishes; block promotion. |
| `durable_ack_p99_high` | coherence/backing_service | Queue or reject KV-D3+. |
| `mesh_quorum_degraded` | coherence | RED for durable classes. |
| `replica_deficit` | coherence | AMBER/RED by class. |
| `backing_degraded` | backing_service | RED for durable/governed writes. |
| `offload_fallback_active` | platform | AMBER/RED; no production promotion. |
| `qat_endpoint_degraded` | platform | Prefer CPU fallback, throttle QAT-dependent paths, or DRAIN affected accelerator scope. |
| `qat_assignment_untrusted` | platform | Reject QAT-dependent placement; require trusted guest/driver-domain reassignment. |
| `qat_pf_vf_map_stale` | platform | Reject or drain QAT-dependent placement until PF/VF ownership epoch is current. |
| `qat_fallback_active` | platform | AMBER/RED by class; no production promotion for QAT-dependent SLOs until remediated. |
| `fabric_congestion_high` | platform | Throttle hydration, reroute, or queue. |
| `cxl_latency_high` | platform/coherence | Prefer DRAM/local placement, throttle CXL-dependent warm-tier use, or queue. |
| `cxl_topology_unqualified` | platform | Reject CXL-dependent placement; require source-of-truth correction or physical re-slotting. |
| `cxl_fabric_manager_unhealthy` | platform | DRAIN affected CXL pool scope; reject CXL-dependent placement until CFM/fabric state is current. |
| `cxl_pool_ownership_stale` | platform/coherence | Fence CXL pool writes and demote warm KV/prefix data to DRAM/T2 where possible. |
| `cxl_hotness_unavailable` | platform/coherence | Disable hotness-guided placement; prefer DRAM for hot regions and lower CXL locality score. |
| `cxl_pressure_high` | platform/coherence | Demote to T2/T3 or reduce warm-tier admission. |
| `cxl_telemetry_stale` | scheduler/platform | Conservative AMBER/RED by class; no CXL-dependent promotion. |
| `power_headroom_low` | platform | Drain background work; protect durable classes. |
| `timing_unvalidated` | platform | Avoid using cross-node timing evidence. |
| `telemetry_stale` | scheduler/platform | Conservative admission by class. |

## Class decision table

| Class | GREEN | AMBER | RED | DRAIN |
| --- | --- | --- | --- | --- |
| KV-D0 | Admit if memory/token budget fits | Reduce concurrency/preemption risk | Reject/queue request | Stop new runtime placement |
| KV-D1 | Admit with locality preference | Recompute if hit is unlikely | Treat cache as miss | Stop cache-dependent placement |
| KV-D2 | Admit reads/writes under lag threshold | Admit reads; throttle writes/promotions | Stop new write-back growth; recompute pending | Flush/drain if safe |
| KV-D3 | Admit durable publishes | Queue/throttle new durable publishes | Reject/queue durable publishes | Drain durable path |
| KV-D4 | Admit with writer epoch | Restrict new writers; allow safe reads | Fence writers and queue | Drain sessions/checkpoint |
| KV-D5 | Admit only with full evidence | Queue only if policy allows | Fail closed | Drain/fail closed |

## Example admission summary

```json
{
  "summary_epoch": 38142,
  "generated_at": "2026-05-13T13:54:37Z",
  "entries": [
    {
      "tenant_id": "lab-system",
      "model_id": "model:sha256:example",
      "durability_class": "KV-D2",
      "prefix_shard": "pfx-017",
      "scope": "rack",
      "state": "AMBER",
      "action": "throttle",
      "freshness_ms": 2800,
      "reason_codes": [
        {
          "code": "writeback_lag_high",
          "owner": "coherence",
          "message": "oldest pending write-back age exceeded class threshold"
        }
      ]
    }
  ]
}
```

## Operating requirements

- Rollup service must publish at least one current summary before scheduler admits production-like traffic.
- Scheduler must reject summaries older than the configured freshness threshold.
- Every admission/rejection decision must include summary epoch, state, action, reason code, and owning subsystem.
- Admission policy versions must be recorded in benchmark and rollout reports.
- Dashboard panels must group by class, model, tenant, scope, reason code, QAT PF/VF profile when QAT participates in the placement, OCP CMS topology class, and CXL topology profile when CXL participates in the placement.
- Rollup logic must be tested with synthetic Coherence, durable backing, offload, QAT endpoint/VF/PF/service/trust/fallback, CXL topology/latency/fabric-manager/ownership/hotness/telemetry, fabric, telemetry, and power/facility fault inputs.

## Verification checklist

- [ ] Coherence lookup/publish/write-back metrics appear in raw metrics.
- [ ] Admission summary endpoint returns GREEN/AMBER/RED/DRAIN entries.
- [ ] Scheduler decision logs include summary epoch.
- [ ] Write-back lag fault changes KV-D2 admission.
- [ ] Durable backing fault blocks KV-D3 through KV-D5 as expected.
- [ ] DPU fallback, QAT endpoint/VF/PF/service/trust faults, CXL topology/latency/fabric-manager/pool-ownership faults, hotness unavailability, and fabric congestion are visible as reason codes.
- [ ] Stale telemetry causes conservative admission.
- [ ] vLLM configuration remains Coherence-only.
