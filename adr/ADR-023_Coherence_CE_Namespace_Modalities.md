# ADR-023: Coherence-CE Namespace Modalities

**Project:** Project Coherent Storage
**Architecture cycle:** 2026-Q2
**Status:** Proposed
**Generated:** 2026-05-18

## Architecture diagram

![ADR-023_Coherence_CE_Namespace_Modalities](diagrams/ADR-023_Coherence_CE_Namespace_Modalities.png)

## Decision summary

Support two explicit Coherence-CE namespace modalities for prefix-cache, object, KV, and vector operations:

1. **Unified Namespace**: one logical namespace per tenant/application scope where Coherence-CE hides placement, routing, and replica locality behind a single global identity space.
2. **Dimensional Indexed Namespace**: a namespace plus a declared dimensional index that partitions lookup and search authority by locality, model/runtime, durability, tenant, epoch, and data-class dimensions.

Exact operations are never keyless. A request that puts, gets, or deletes a prefix-cache artifact must carry a `prefix_id`. Keyless collection routes are valid only for search and predicate/bulk invalidation.

## Context

The S3/Object-to-REST translator design and the ADR text previously described prefix-cache routes in two incompatible ways. One document implied a single `/prefix-cache/{namespace}` endpoint family for put/get/search/invalidate, while another required `/prefix-cache/{namespace}/{prefix_id}` for exact object operations and `/search` for collection search. That mismatch is unsafe for implementers because OpenAPI generation, SDK construction, authorization policy, cache correctness, and idempotency behavior all depend on whether a request is exact-object scoped or collection scoped.

Project Coherent Storage also needs two namespace operating models. Inter-datacenter and intra-datacenter latency are materially different. A single global cache namespace is simple for clients, but global lookup and invalidation can create tail-latency and blast-radius problems when transaction locality shifts between regions, datacenters, pods, racks, and Coherence-CE mesh pools. A dimensional index lets the architecture scale out and scale up by making locality and compatibility dimensions explicit without exposing OpenZFS, DPU, RDMA, CXL, or physical storage internals to inference actors.

## Decision

### Modality A: Unified Namespace

A Unified Namespace presents one logical namespace string to clients and adapters. Coherence-CE owns routing and may internally map the namespace to region, datacenter, mesh-pool, rack, pod, tenant, model, and durability authorities.

Use Unified Namespace when:

- clients need the simplest stable contract;
- transaction locality is mostly local or Coherence-CE can route it predictably;
- global identity is more important than exposing index shape;
- the workload can tolerate Coherence-CE doing a global or hierarchical lookup; or
- a migration period requires compatibility with existing namespace strings.

Canonical route shape for prefix-cache operations:

| Operation class | Method | Path | Scope |
| --- | --- | --- | --- |
| Exact put | `PUT` | `/prefix-cache/unified/{namespace}/prefixes/{prefix_id}` | One prefix artifact. |
| Exact get | `GET` | `/prefix-cache/unified/{namespace}/prefixes/{prefix_id}` | One prefix artifact. |
| Exact delete | `DELETE` | `/prefix-cache/unified/{namespace}/prefixes/{prefix_id}` | One prefix artifact. |
| Collection search | `POST` | `/prefix-cache/unified/{namespace}/search` | Namespace search using explicit query body. |
| Predicate invalidate | `POST` | `/prefix-cache/unified/{namespace}/invalidate` | Namespace bulk invalidation by predicate, epoch, or policy. |

Unified Namespace requests may include route hints, but hints are advisory. Coherence-CE may ignore hints when policy, admission, durability, or locality state requires a different route.

### Modality B: Dimensional Indexed Namespace

A Dimensional Indexed Namespace adds an `index_id` path segment and a request-visible `namespace_descriptor` that names the index dimensions used to scope lookup/search authority. The `index_id` is a stable URL-safe token derived from or mapped to a declared dimension set; it is not a physical path, zpool, RDMA queue pair, VLAN, CXL device, or DPU identifier.

Use Dimensional Indexed Namespace when:

- inter-datacenter or cross-region prefix-cache lookup adds unacceptable TTFT or TPOT tail latency;
- operational locality changes over time and needs epoch-aware routing;
- cache authority should be scoped to a region, datacenter, pod, rack, mesh pool, model family, tenant, or durability class;
- search must stay local first and escalate only on miss or policy approval;
- invalidation blast radius must be bounded; or
- the scheduler needs locality-aware admission summaries.

Canonical route shape for prefix-cache operations:

| Operation class | Method | Path | Scope |
| --- | --- | --- | --- |
| Exact put | `PUT` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/prefixes/{prefix_id}` | One prefix artifact in one declared index. |
| Exact get | `GET` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/prefixes/{prefix_id}` | One prefix artifact in one declared index. |
| Exact delete | `DELETE` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/prefixes/{prefix_id}` | One prefix artifact in one declared index. |
| Indexed search | `POST` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/search` | Index-local search with optional escalation policy. |
| Indexed invalidate | `POST` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/invalidate` | Index-local predicate invalidation. |

Recommended dimensions:

| Dimension | Purpose |
| --- | --- |
| `tenant_id` | Tenant, project, or requester isolation boundary. |
| `region` | Global geography or business continuity domain. |
| `datacenter` | Datacenter-local authority and latency boundary. |
| `mesh_pool` | Coherence-CE mesh pool or locality authority. |
| `pod` / `rack` | Intra-datacenter topology locality for accelerator/storage placement. |
| `model_id` / `tokenizer_id` / `adapter_id` | Compatibility boundary for safe prefix reuse. |
| `runtime_profile_hash` | KV layout, attention backend, block size, dtype, and runtime compatibility. |
| `durability_class` | KV-D0 through KV-D5 persistence and recovery semantics. |
| `locality_epoch` | Routing epoch used when transactions move between locality domains. |
| `data_class` | `kv`, `prefix`, `object`, `vector`, `metadata`, or `checkpoint`. |

## API invariants

- `PUT`, exact `GET`, and exact `DELETE` require `prefix_id`.
- `POST /search` is collection scoped and must carry a search body.
- `POST /invalidate` is collection scoped and must carry a bounded predicate, epoch, or object-list body.
- `/prefix-cache/{namespace}` must not be used as an overloaded exact-operation family.
- Legacy `/prefix-cache/{namespace}/{prefix_id}` can exist only as a documented compatibility alias that resolves to Unified Namespace semantics; new generated clients must use the explicit modality routes.
- Inference actors still call Coherence-CE. They do not see OpenZFS datasets, NVMe-oF namespaces, RDMA handles, DPU queue pairs, CXL device IDs, VLANs, or storage nodes.

## Workflow semantics

### Unified Namespace lookup

1. Client supplies `namespace`, `prefix_id`, identity, runtime profile, durability class, and context.
2. Coherence-CE checks namespace policy and tenant authorization.
3. Coherence-CE resolves the current authoritative mesh pool or replica set.
4. Exact lookup returns hit, miss, stale, incompatible profile, or degraded.
5. Search stays namespace scoped and may perform hierarchical local-to-global escalation internally.

### Dimensional Indexed lookup

1. Client supplies `namespace`, `index_id`, `prefix_id`, identity, runtime profile, dimensions, durability class, and context.
2. Coherence-CE validates that `index_id` matches or is authorized for the declared dimensions.
3. Lookup is attempted in the indexed locality authority first.
4. Search and invalidation remain bounded to the index unless the request includes an authorized escalation policy.
5. Scheduler admission consumes index-local hit rate, p99 hydration latency, dirty bytes, DPU/OpenZFS health, and fabric/CXL telemetry as scoped metrics.

## Failure and locality behavior

| Failure or locality event | Unified Namespace behavior | Dimensional Indexed Namespace behavior |
| --- | --- | --- |
| Local mesh-pool miss | Coherence-CE may search other pools internally. | Miss stays index-local unless escalation is authorized. |
| Cross-region latency spike | Coherence-CE may demote the namespace or reroute. | Affected region/datacenter index can be AMBER/RED while other indexes stay GREEN. |
| Locality epoch change | Namespace authority updates internally. | `locality_epoch` changes, old index can drain, new index can warm. |
| Invalidation request | Global predicate must be carefully bounded. | Predicate is index-local by default, reducing blast radius. |
| Datacenter isolation | Namespace may enter degraded global mode. | Local indexes can continue for classes that permit regional authority. |
| Stale index telemetry | Coherence-CE must not infer health from silence. | Index enters AMBER/RED/DRAIN until telemetry freshness recovers. |

## Consequences

### Positive

- Client generation has an unambiguous prefix-cache contract.
- Global simplicity and locality-indexed scale are both supported.
- Cross-datacenter cache operations can be bounded by declared locality and escalation policy.
- Scheduler admission can reason about cache locality without exposing physical storage internals.
- Invalidation, search, and failure blast radius become explicit design choices.

### Negative

- Dimensional indexes add governance work: dimension definition, index lifecycle, epoch rotation, telemetry rollup, and compatibility testing.
- Operators must prevent index proliferation and stale dimensions.
- Compatibility aliases can confuse implementers if not marked as deprecated.

### Deferred

- Automatic dimension selection from live scheduler traces.
- Formal index compaction and archival policy.
- Cross-region conflict-resolution protocol for multi-authority writes.
- SDK helpers that derive `index_id` from a signed namespace descriptor.

## Acceptance criteria

- The REST translator OpenAPI document exposes explicit Unified Namespace and Dimensional Indexed Namespace prefix-cache paths.
- ADR-012 includes namespace modality in KV identity or request context without exposing physical infrastructure details.
- ADR-022 and the translator design report no longer define `/prefix-cache/{namespace}` as a keyless exact-operation family.
- Diagrams and README links use `adr/diagrams/` for ADR diagram assets.
- Search and invalidate are documented as collection operations; exact put/get/delete require `prefix_id`.

## Related files

- `adr/ADR-012_Coherence_CE_vLLM_Adapter_API_Contract.md`
- `adr/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.md`
- `api/coherence-ce-vllm-adapter.openapi.yaml`
- `api/s3-object-rest-translator.openapi.yaml`
- `reports/project-coherent-storage_s3-object-rest-api-translator-design.md`
