# ADR-012: Coherence-CE vLLM Adapter API Contract

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Architecture diagram

![ADR-012_Coherence_CE_vLLM_Adapter_API_Contract](diagrams/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.png)

## Decision summary

Expose an exact Coherence-CE API contract to vLLM adapters and OpenAI-compatible gateways. vLLM and peer inference actors call Coherence-CE only. They receive hit/miss/payload/durability/admission semantics and never receive lower-layer storage, DPU, NVMe-oF, RoCEv2, or RDMA configuration.

## Context

vLLM-compatible serving stacks commonly expose OpenAI-compatible `/v1/chat/completions` semantics and increasingly need compatibility with `/v1/responses`. The OpenAI OpenAPI specification defines Chat Completions as returning a chat completion object or streamed chat completion chunk objects; it also defines Responses as returning response objects or response stream events. Project Coherent Storage must preserve these client-facing model APIs while adding a Coherence-native KV contract for adapters that need prefix lookup, publish, promotion, and admission signals.

The key boundary is architectural: inference clients can know that Coherence-CE can provide correct KV/prefix data, but they must not know how Coherence-CE persists or hydrates that data through OpenZFS, DPU-handled NVMe-oF/RoCEv2, or RDMA paths.

## Decision

- Provide two compatible API planes:
  - **OpenAI-compatible inference plane:** `/v1/chat/completions` and `/v1/responses` remain standard-shaped model APIs.
  - **Coherence-native KV plane:** `/v1/coherence/*` endpoints support vLLM adapter lookup, publish, reserve, flush, promote, evict, health, and admission summary operations.
- Allow OpenAI-compatible requests to carry Coherence hints only as opaque metadata or headers that do not expose lower-layer internals.
- Require vLLM adapters to configure only Coherence-CE endpoint, credentials, model/runtime profile, timeout, and default durability class.
- Define all adapter-visible errors as API-layer reasons: `miss`, `stale`, `incompatible_profile`, `durability_unavailable`, `admission_rejected`, `quota_exceeded`, `mesh_degraded`, or `timeout`.
- Carry namespace modality as a logical Coherence-CE descriptor only: `unified` or `dimensional_indexed`. The descriptor may include `namespace`, `index_id`, and dimensions, but must never expose lower-layer storage or fabric identifiers.
- Publish the OpenAPI 3.1 contract in `api/coherence-ce-vllm-adapter.openapi.yaml`.

## OpenAI-compatible inference plane

The inference gateway may accept standard OpenAI-compatible requests:

- `POST /v1/chat/completions`
- `POST /v1/responses`

The gateway may map request metadata into Coherence-CE policy context. Allowed metadata/header examples:

| Field | Meaning |
| --- | --- |
| `metadata.coherence.session_id` | Stable session/workflow identity used for KV-D4 session routing. |
| `metadata.coherence.durability_class` | Requested class such as `KV-D1` or `KV-D3`, subject to tenant policy. |
| `metadata.coherence.prefix_policy` | `default`, `reuse_preferred`, `no_store`, or `durable_required`. |
| `metadata.coherence.trace_id` | Request trace correlation ID. |
| `Idempotency-Key` | Publish/retry deduplication for gateway-managed operations. |
| `OpenAI-Project` or tenant header equivalent | Tenant/project policy binding when present in the deployment. |

The gateway must ignore or reject any client-provided metadata that attempts to select storage devices, pools, namespaces, queue pairs, rkeys, fabric classes, or offload hardware. Such fields are control-plane internals and are not part of OpenAI-compatible request semantics.

## Coherence-native KV plane

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/v1/coherence/kv/lookup` | POST | Resolve one or more prefix/KV identities to hit/miss/payload references. |
| `/v1/coherence/kv/publish` | POST | Publish computed KV/prefix blocks with a durability class and idempotency key. |
| `/v1/coherence/kv/reserve` | POST | Reserve expected KV growth or a session writer epoch before admission. |
| `/v1/coherence/kv/flush` | POST | Request write-back flush for pending KV-D2 or higher objects. |
| `/v1/coherence/kv/promote` | POST | Promote an object to a stronger durability class after policy checks. |
| `/v1/coherence/kv/evict` | POST | Evict, demote, or invalidate KV objects by identity/policy. |
| `/v1/coherence/kv/health` | GET | Return Coherence-CE mesh and KV-service health summary. |
| `/v1/coherence/admission/summary` | GET | Return scheduler-facing admission rollup by model, tenant, class, and locality scope. |

## Request identity

Every lookup and publish must include a compatible KV identity:

| Field | Requirement |
| --- | --- |
| `model_id` | Content-addressed model manifest ID. |
| `tokenizer_id` | Tokenizer version and vocabulary hash. |
| `adapter_id` | Adapter/LoRA hash or `none`. |
| `runtime_profile.engine` | Runtime such as `vllm`. |
| `runtime_profile.attention_backend` | Attention implementation/profile. |
| `runtime_profile.block_size` | Logical KV block size. |
| `runtime_profile.dtype` | KV dtype or quantized format. |
| `runtime_profile.layout_version` | Coherence/vLLM layout compatibility version. |
| `prefix_hash` | Hash of normalized token prefix plus policy salt. |
| `block_range` | Logical block range or block index. |
| `placement_epoch` | Optional epoch; required for extendable/session state. |
| `namespace_descriptor.mode` | `unified` or `dimensional_indexed`; defaults to `unified` when absent by policy. |
| `namespace_descriptor.namespace` | Logical Coherence-CE namespace. |
| `namespace_descriptor.index_id` | Required for dimensional indexed operations; not a physical path, DPU, RDMA, VLAN, CXL, or zpool identifier. |
| `namespace_descriptor.dimensions` | Optional tenant, region, datacenter, mesh pool, pod, model/runtime, durability, data-class, and locality-epoch dimensions. |

## Namespace modality contract

ADR-023 defines the two namespace modalities used by Coherence-CE and the S3/Object REST translator. The vLLM adapter contract exposes only the logical descriptor:

| Modality | Adapter-visible meaning | Lower-layer exposure |
| --- | --- | --- |
| `unified` | One logical namespace; Coherence-CE hides locality and routing. | None. |
| `dimensional_indexed` | Namespace plus `index_id` and declared dimensions for locality-aware lookup/admission. | None. |

The adapter may request a namespace descriptor to preserve cache locality, but Coherence-CE remains authoritative. Policy may rewrite, reject, drain, or degrade a descriptor when telemetry, durability, tenant isolation, or failure semantics require it.

## Response contract

Coherence-CE lookup responses return:

- `status`: `hit`, `miss`, `stale`, `incompatible_profile`, `recompute_required`, or `degraded`.
- `durability_class`: KV-D0 through KV-D5.
- `durability_state`: `volatile`, `mesh_committed`, `writeback_pending`, `durable`, `degraded`, or `rejected`.
- `payload`: inline bytes only for small test/canary payloads, or a Coherence-generated object reference for larger blocks.
- `expires_at` and `epoch` when applicable.
- `admission_hint`: scheduler-facing summary such as `admit`, `queue`, `recompute`, `throttle`, or `reject`.
- `diagnostics`: API-layer reason codes only.

Payload references are Coherence-CE references. They are not OpenZFS paths, NVMe-oF namespaces, RDMA handles, DPU handles, or fabric routes.

## S3-object-style translation

Coherence-CE may expose an S3-object-style REST translation for runtimes that prefer object payload flows. This translation remains a Coherence-CE API. Object keys are logical Coherence object IDs, not filesystem paths or block-device identifiers. The translation must preserve the same identity, namespace modality, durability, authorization, and audit semantics as the native KV endpoints.

The translator API must not offer ambiguous keyless exact prefix-cache operations. Exact put/get/delete operations require `prefix_id`; search and predicate invalidation use collection routes with request bodies.

## Error semantics

| HTTP status | Coherence error | Meaning |
| --- | --- | --- |
| 400 | `invalid_identity` | Required identity fields are missing or malformed. |
| 401/403 | `unauthorized` / `forbidden` | Tenant, model, class, or session policy rejects access. |
| 404 | `miss` | No compatible object exists; recompute may be allowed. |
| 409 | `stale` / `epoch_conflict` | Object exists but version/epoch is unsafe for serving. |
| 412 | `incompatible_profile` | Model/tokenizer/adapter/runtime profile does not match. |
| 425 | `durability_pending` | Durable class requested but write-back/flush has not completed. |
| 429 | `admission_rejected` / `quota_exceeded` | Scheduler or policy throttled the operation. |
| 503 | `mesh_degraded` / `durability_unavailable` | Coherence or backing durability is unavailable for requested class. |
| 504 | `timeout` | Operation exceeded client or service deadline. |

## Positive consequences

- vLLM adapters have a precise, testable API contract.
- OpenAI-compatible clients can remain unaware of Coherence-CE unless they opt into metadata hints.
- Storage and fabric internals remain behind the mesh, preserving layer separation.
- API responses expose enough state for correct recompute and admission behavior without leaking implementation control.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| OpenAI-compatible metadata becomes an unbounded control API | Whitelist metadata keys and reject lower-layer terms or unrecognized policy fields. |
| vLLM adapters depend on object-reference internals | Treat object references as opaque, scoped, expiring Coherence tokens. |
| API shape drifts from OpenAI compatibility | Keep `/v1/chat/completions` and `/v1/responses` standard-shaped; keep Coherence operations under `/v1/coherence/*`. |
| Runtime upgrades break KV layout | Include runtime profile and layout version in every identity. |

## Acceptance criteria

- `api/coherence-ce-vllm-adapter.openapi.yaml` parses as OpenAPI 3.1 YAML.
- KV identity and context schemas include a logical namespace descriptor for Unified Namespace and Dimensional Indexed Namespace operation.
- vLLM adapter setup requires only Coherence-CE endpoint/protocol credentials and runtime profile.
- OpenAI-compatible Chat/Responses requests can pass optional Coherence hints without changing standard response shape.
- Lower-layer storage/fabric/offload identifiers are absent from request and response schemas.
- Wrong-version and incompatible-profile canaries return explicit API errors rather than serving data.

## Source documents

| ID | Use |
| --- | --- |
| R01 | vLLM KV block identity, paged KV sharing, and preemption behavior. |
| R02, R03 | Serving API, scheduler, TTFT/TPOT, and runtime interaction context. |
| O08 | OpenAI Chat Completions OpenAPI shape, response object, and streaming chunk behavior. |
| O09 | OpenAI Responses OpenAPI shape and stream-event behavior. |
| O01, O03 | Coherence REST/API and metrics context for Coherence-owned service endpoints. |
