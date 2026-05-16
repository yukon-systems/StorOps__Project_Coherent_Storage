# OpenAI-Compatible Extension Contract

**Project:** Project Coherent Storage  
**Version:** 2026-Q2  
**Package:** v2 inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Purpose

This document defines how OpenAI-compatible clients and vLLM adapters interact with Coherence-CE without learning the storage or network implementation below Coherence-CE.

## Client-facing model APIs

Project Coherent Storage may expose standard OpenAI-compatible endpoints:

- `POST /v1/chat/completions`
- `POST /v1/responses`

These endpoints keep standard response shapes. Chat Completions returns chat completion objects or stream chunks. Responses returns response objects or stream events. Coherence-specific behavior must not require clients to parse nonstandard completion payloads.

## Allowed extension points

OpenAI-compatible callers may provide optional hints in metadata or headers. These hints are policy requests, not commands.

| Extension | Example | Meaning |
| --- | --- | --- |
| `metadata.coherence.session_id` | `agent-run-2026-05-13-001` | Bind request to KV-D4 session context when tenant policy allows. |
| `metadata.coherence.durability_class` | `KV-D2` | Request a class; Coherence-CE may downgrade, reject, or override by policy. |
| `metadata.coherence.prefix_policy` | `reuse_preferred` | Hint for lookup/publish behavior. |
| `metadata.coherence.trace_id` | `trace-01HX...` | Correlate gateway, scheduler, Coherence, and runtime logs. |
| `Idempotency-Key` | opaque UUID | Deduplicate gateway-mediated publishes or retries. |
| tenant/project header | deployment-specific | Select tenant policy and quota. |

Allowed `prefix_policy` values:

- `default`
- `reuse_preferred`
- `no_store`
- `durable_required`

## Forbidden extension points

OpenAI-compatible clients, vLLM adapters, and peer inference actors must not send or require any of these lower-layer controls:

- OpenZFS pool, dataset, zvol, vdev, SLOG, ARC, scrub, resilver, recordsize, or sync-property selectors;
- NVMe-oF subsystem, namespace, ANA, queue-depth, initiator, target, or path selectors;
- DPU or SmartNIC device, firmware, queue, offload service, or fallback selectors;
- QAT device, driver, firmware, PF/VF, service, rate-limit, reset, or fallback selectors;
- CXL device, pool, switch, root-complex, bifurcation, fabric-manager, hotness, or migration selectors;
- RoCEv2, RDMA, rkey, memory-region, queue-pair, completion-queue, PFC, ECN, CNP, or rail selectors;
- rack power, PSU, ESS, timing, or management-channel override fields.

Those signals are owned by Coherence-CE, storage services, fabric services, platform services, and scheduler admission. The inference client sees only policy-level acceptance, rejection, recompute, queue, throttle, or degraded results.

## Gateway behavior

1. Accept standard OpenAI-compatible request.
2. Extract allowed metadata and headers.
3. Resolve tenant/model/runtime policy.
4. Ask Coherence-CE for admission and prefix lookup when applicable.
5. Route to vLLM or peer runtime with only Coherence-CE endpoint/protocol credentials and runtime profile.
6. Publish reusable KV/prefix state back through Coherence-CE when runtime policy allows.
7. Return standard OpenAI-compatible response or stream.

## vLLM adapter behavior

A vLLM adapter may call the Coherence-native API directly:

- lookup before or during prefill;
- reserve expected KV capacity before admission;
- publish reusable prefix blocks after prefill;
- flush or promote when policy asks for stronger durability;
- evict or demote when runtime memory pressure requires it;
- read health/admission summaries for local throttling.

Adapter configuration contains:

- `COHERENCE_CE_BASE_URL`;
- Coherence-CE credentials;
- timeout/retry budget;
- runtime profile and layout version;
- default durability class or tenant policy reference.

Adapter configuration does not contain OpenZFS, NVMe-oF, DPU, QAT, CXL, RoCEv2, or RDMA configuration.

## Error mapping

| Coherence-native reason | OpenAI-compatible handling |
| --- | --- |
| `miss` | Recompute/prefill if request budget allows; no client-visible error needed. |
| `stale` | Treat as miss or internal error depending on policy; never serve stale KV. |
| `incompatible_profile` | Treat as miss if recompute allowed; otherwise fail request with explicit internal incompatibility. |
| `durability_pending` | Continue only if requested class allows pending state; otherwise queue/timeout. |
| `durability_unavailable` | Reject/queue durable-required requests. |
| `admission_rejected` | Return gateway overload, queue, or retryable rejection according to tenant contract. |
| `mesh_degraded` | Route to alternate locality or queue/recompute. |
| `telemetry_stale` | Conservative admission; no durable/governed promotion. |

## Compatibility rule

OpenAI-compatible endpoints are compatibility surfaces, not storage-control surfaces. Any feature that requires storage/fabric/offload control belongs under Coherence-CE or scheduler APIs and must remain invisible to OpenAI-compatible callers.

## Source references

- O08: OpenAI Chat Completions OpenAPI spec.
- O09: OpenAI Responses OpenAPI spec.
- ADR-005: DPU, SmartNIC, and QAT offload boundaries.
- ADR-012: Coherence-CE vLLM Adapter API Contract.
- ADR-014: Coherence Metrics to Scheduler Admission.
- R251/R252: BMRA/QAT host accelerator evidence used only below the Coherence-CE contract.
