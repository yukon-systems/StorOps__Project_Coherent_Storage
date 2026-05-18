# ADR-014: Coherence Metrics to Scheduler Admission

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Roll Coherence-CE metrics into scheduler admission through a normalized health and locality summary. The scheduler consumes Coherence-owned service signals, not raw vLLM guesses and not lower-layer storage/fabric internals. Admission states are GREEN, AMBER, RED, and DRAIN by model, tenant, durability class, prefix shard, locality scope, and time window.

## Context

ADR-007 already makes scheduler admission storage-aware. ADR-009 defines required metric families. The missing operating requirement is the exact modality by which Coherence-CE metrics become admission inputs. Coherence documentation exposes metrics in Prometheus/JSON-compatible forms, while OpenZFS and fabric layers expose pool, scrub/resilver, queue, congestion, and latency signals below Coherence-CE. Coherence-CE must summarize those lower-layer signals into scheduler-safe facts without making vLLM or the scheduler directly program lower layers.

## Decision

- Coherence-CE publishes raw service metrics and a normalized admission summary.
- A rollup service aggregates Coherence, OpenZFS-backed durability, DPU/offload, QAT accelerator, CXL tier/topology, fabric, and telemetry freshness signals into scheduler-facing states.
- Scheduler admission consumes only normalized summaries and decision logs with layer ownership preserved.
- Missing required Coherence metrics are admission blockers for affected classes/scopes.
- The rollup state must be class-aware: KV-D0/KV-D1 may continue during some durability faults; KV-D3 through KV-D5 require durable evidence.

## Metrics families

| Family | Metrics |
| --- | --- |
| Lookup/hydration | `lookup_total`, `hit_total`, `miss_total`, `stale_reject_total`, `incompatible_profile_total`, `lookup_latency_ms`, `hydrate_latency_ms` |
| Publish/write policy | `publish_total`, `publish_latency_ms`, `write_policy`, `durability_state`, `durable_ack_latency_ms` |
| Write-back | `writeback_queue_records`, `writeback_queue_bytes`, `oldest_writeback_age_ms`, `writeback_retry_total`, `writeback_failure_total`, `durable_lag_ms` |
| Mesh health | `mesh_member_count`, `partition_primary_count`, `partition_backup_count`, `ownership_epoch`, `replica_deficit_total`, `quorum_state` |
| KV memory | `kv_bytes_by_class`, `kv_blocks_by_class`, `eviction_total`, `protected_prefix_count`, `recompute_total` |
| QAT accelerator | `qat_device_state`, `qat_service_state`, `qat_driver_version`, `qat_firmware_version`, `qat_pf_vf_map_epoch`, `qat_trust_scope`, `qat_endpoint_error_total`, `qat_reset_total`, `qat_crypto_error_total`, `qat_compression_error_total`, `qat_utilization`, `qat_rate_limit_state`, `qat_fallback_state`, `qat_telemetry_age_ms` |
| CXL tier/topology | `cxl_capacity_bytes`, `cxl_pressure`, `cxl_latency_ms`, `cxl_bandwidth_bytes`, `cxl_numa_distance`, `cxl_root_complex`, `cxl_generation`, `cxl_link_width`, `cxl_link_speed`, `cxl_switch_hops`, `cxl_bifurcation_state`, `cxl_error_total`, `cxl_thermal_state`, `cxl_telemetry_age_ms` |
| CXL fabric/pool management | `cxl_fabric_manager_state`, `cxl_cfm_api_age_ms`, `cxl_pool_ownership_epoch`, `cxl_pool_fence_state`, `cxl_hotness_state`, `cxl_migration_queue_records`, `cxl_compression_ratio`, `cxl_ras_event_total` |
| Backing durability summary | `backing_state`, `backing_commit_latency_ms`, `backing_error_total`, `scrub_resilver_state`, `pool_degraded` |
| Offload/fabric summary | `offload_state`, `fallback_state`, `fabric_congestion_state`, `path_failover_total`, `rtt_ms`, `drop_or_timeout_total` |
| Scheduler outcomes | `admission_state`, `admit_total`, `queue_total`, `reject_total`, `throttle_total`, `drain_total`, `reason_code` |
| Freshness | `last_sample_age_ms`, `rollup_age_ms`, `source_missing_total`, `clock_state` |

## Rollup intervals and freshness

| Signal | Raw interval target | Rollup window | Freshness rule |
| --- | --- | --- | --- |
| Coherence lookup/publish latency | 1s to 5s | 10s / 60s p95-p99 | stale above 2 rollup windows |
| Write-back lag/queue age | 1s to 5s | latest plus 60s trend | stale above 15s for KV-D2+ |
| Mesh quorum/partition ownership | event plus 1s poll | latest | stale above 5s for durable classes |
| Backing durability/pool health | 5s to 30s | latest plus 5m trend | stale above 60s for KV-D3+ |
| DPU/offload/fabric state | 1s to 10s | latest plus 60s trend | stale above 30s for storage-path admission |
| QAT device/service/VF/PF state | 1s to 10s plus event stream for reset/VF/PF changes | latest plus 60s trend; PF/VF map epoch | stale above 30s for QAT-dependent admission; untrusted assignment is RED |
| CXL capacity/topology/latency | 1s to 10s for pressure/latency; event plus inventory for topology | latest plus 60s trend; inventory epoch | stale above policy threshold; unqualified topology is RED for CXL-dependent placement |
| CXL fabric manager, pool ownership, hotness, and migration | 1s to 10s plus event stream | latest plus 60s trend; ownership epoch | stale or ambiguous ownership is RED for CXL-dependent placement and DRAIN for affected pool writes |
| Rack/power/timing/management | 10s to 60s | latest plus maintenance window | stale above policy threshold; never assumed healthy |

## Admission states

| State | Meaning | Scheduler behavior |
| --- | --- | --- |
| GREEN | SLO, durability, quorum, and freshness requirements are satisfied for class/scope | Admit normally and prefer locality/hit score |
| AMBER | Service is safe but degraded, near threshold, stale for noncritical class, or under maintenance | Admit only classes allowed by policy; throttle writes/prefetch/rebuild |
| RED | Correctness, durability, quorum, or SLO evidence is insufficient for class/scope | Reject, queue, or force recompute depending on class |
| DRAIN | Planned or reactive drain; existing safe work may complete, new work stops | Stop new placement; move traffic; preserve evidence |

## Class-aware admission rules

| Condition | KV-D0/KV-D1 | KV-D2 | KV-D3 | KV-D4 | KV-D5 |
| --- | --- | --- | --- | --- | --- |
| Mesh healthy, backing healthy | GREEN | GREEN | GREEN | GREEN | GREEN |
| Write-back lag high | GREEN if memory safe | AMBER/RED by lag threshold | AMBER for new publishes | AMBER if checkpoint lag affected | RED if retention affected |
| Backing durability unavailable | GREEN for recompute | AMBER; pending data treated recomputable | RED for new durable publishes | RED for checkpoints/new writers | RED/fail closed |
| Coherence quorum degraded | AMBER/RED by replica policy | AMBER/RED | RED unless durable read proof exists | RED/fence | RED/fail closed |
| DPU fallback active | AMBER if unaffected | AMBER | AMBER/RED by durable latency | RED if epoch/checkpoint path affected | RED unless approved contingency |
| QAT unavailable or endpoint degraded | AMBER if CPU fallback preserves SLO | AMBER/RED if compression/crypto path affected | AMBER/RED for QAT-dependent durable transforms; otherwise CPU fallback | RED if session/checkpoint crypto/compression depends on QAT and fallback is not qualified | RED/fail closed if retention/audit crypto depends on QAT and fallback evidence is absent |
| QAT assignment untrusted or PF/VF map ambiguous | RED for QAT-dependent placement | RED for QAT-dependent placement | RED for new QAT-dependent writes | RED/fence QAT-dependent writers | RED/fail closed |
| Fabric congestion high | AMBER by TTFT/TPOT budget | AMBER/RED by hydration lag | AMBER/RED by durable write p99 | RED if writer path unsafe | RED if audit path unsafe |
| CXL topology unqualified or latency high | AMBER if CXL not required | AMBER/RED by hydration role | RED for new durable writes if CXL is in the path | RED for CXL-dependent writers | RED/fail closed if CXL is required for retention/audit |
| CXL fabric manager unhealthy or pool ownership stale | AMBER if CXL not required | AMBER/RED by hydration role | RED for CXL-dependent durable writes | RED/fence CXL-dependent writers | RED/fail closed if retention/audit depends on CXL |
| Telemetry stale | AMBER | AMBER/RED | RED for new durable writes | RED for writer admission | RED/fail closed |

## Scheduler summary API

Coherence-CE exposes `GET /v1/coherence/admission/summary` with:

- `summary_epoch` and `generated_at`;
- admission entries by tenant, model, durability class, prefix shard, locality scope, and endpoint;
- current state: GREEN, AMBER, RED, or DRAIN;
- reason codes and owning subsystem;
- SLO estimates for lookup, hydration, publish, durable ack, and recompute;
- freshness for every source family;
- QAT accelerator health, PF/VF map epoch, trusted-assignment state, endpoint/reset/error state, utilization/rate-limit state where supported, and CPU fallback posture when QAT participates in the selected path;
- CXL tier/topology penalties when CXL is part of the selected Coherence/OpenZFS/DPU/GPU path;
- CXL fabric-manager state, CFM/API freshness, pool ownership epoch, hotness/migration state, compression ratio where applicable, and RAS/error state for any CXL pooled-memory placement;
- recommended action: `admit`, `prefer_local`, `queue`, `throttle`, `recompute`, `drain`, or `reject`.

Scheduler decisions must log the summary epoch consumed so post-incident review can connect admission behavior to Coherence state.

## Operating requirements

- Coherence-CE metrics are authoritative for KV locality and durability state.
- Lower-layer OpenZFS, DPU, QAT, CXL, and fabric telemetry is collected by owning services and summarized into Coherence/scheduler-safe states.
- Metric labels must bound cardinality: tenant, model, durability class, endpoint, prefix shard, scope, and reason code are allowed; raw prefix hashes are sampled or redacted in general metrics.
- Admission policy changes are versioned and reversible.
- A missing metric source is not interpreted as healthy.
- Decision logs are retained long enough to cover failure-drill and incident-review windows.
- QAT-backed admission requires current hardware/source-of-truth: device model, integrated/AIC form, PF/VF ownership, trusted guest/driver-domain assignment, driver and firmware version, kernel/VM machine type where passthrough is used, service state, telemetry endpoint, and CPU fallback.
- CXL-backed admission requires current hardware source-of-truth: OCP CMS topology class, socket/root complex, NUMA node, switch hop count, bifurcation, link width/speed, generation, firmware, fabric manager/CFM endpoint, ownership epoch, and telemetry endpoint.

## Positive consequences

- Scheduler can protect TTFT/TPOT and durability guarantees before work is admitted.
- Operators can see whether a rejection came from KV locality, write-back lag, durable backing, offload, fabric, power, timing, or telemetry freshness.
- vLLM remains decoupled from storage/fabric internals.
- Rollout gates become executable and auditable.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Metrics cardinality explodes | Use shard IDs and sampled hashes instead of raw prefix IDs in high-volume metrics. |
| Rollup hides important layer-specific failure | Include owning subsystem and source freshness in every reason code. |
| Scheduler overreacts to transient spikes | Use class-specific windows and hysteresis, but fail closed for durable/governed classes. |
| Stale data causes unsafe admission | Require summary epoch/freshness checks and conservative defaults. |
| Operators bypass Coherence summary | Make Coherence admission summary the scheduler contract; lower-layer metrics remain diagnostic inputs. |
| QAT metrics report utilization but not safety | Require trust scope, PF/VF ownership, endpoint/reset state, driver/firmware version, and fallback state in addition to utilization. |
| CXL topology metrics are present but not actionable | Convert CXL latency, pressure, topology, fabric-manager state, pool ownership, hotness, migration, and telemetry freshness into reason codes and class-aware AMBER/RED/DRAIN actions. |

## Acceptance criteria

- Coherence-CE exports lookup, publish, write-back, mesh, durability, memory, and freshness metrics.
- Scheduler consumes a normalized admission summary rather than direct vLLM or storage-layer guesses.
- Admission decisions record summary epoch, state, reason code, owning subsystem, and action.
- Missing Coherence metrics block production-like promotion for affected paths.
- Failure drills demonstrate GREEN to AMBER/RED/DRAIN transitions for write-back lag, OpenZFS degradation, DPU fallback, QAT endpoint/VF/PF/service faults, CXL topology/latency/fabric-manager/pool-ownership faults, fabric congestion, and telemetry stale events.

## Source documents

| ID | Use |
| --- | --- |
| R02, R03, R30 | Scheduler, TTFT/TPOT, adaptive/proactive placement, and inference service metrics. |
| R01, R25, R26, R27 | KV memory, quantized KV, and cache-hit behavior to expose in metrics. |
| R10, R11, R12, R13, R18, R19, R20, R34, R37 | Fabric, rack, gateway, lifecycle, and observability signals. |
| R22, R23, R31, R32, R33, R35, R36, R40, R41, R42 | OpenZFS, power, timing, management, and facility signals that affect admission. |
| R251, R252 | BMRA telemetry-aware scheduling plus QAT health, trust, VF/PF, driver/firmware, endpoint, reset, and fallback signals. |
| R28, R29, O10, O11, O14-O29, ADR-015 | CXL metrics, topology, pressure, fabric-manager, hotness, pool ownership, and role-governance inputs to admission rollup. |
| O03 | Coherence metrics endpoint and Prometheus/JSON export posture. |
| O06, O07 | OpenZFS scrub/resilver and ZIO scheduler metrics relevant to admission. |
