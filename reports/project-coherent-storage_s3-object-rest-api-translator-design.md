# Project Coherent Storage: S3-Object to REST-API Protocol Mapping Translator

**Project:** Project Coherent Storage
**Sub-focus:** Key-value vector database operations with LLM prompt-prefix caching
**Status:** Proposed design package
**Generated:** 2026-05-17
**Revised:** 2026-05-18

## 1. Purpose

This design defines a portable Python protocol translator that maps S3 object-protocol calls into REST API operations and exposes REST-native CRUD, key/value, vector, and LLM prompt-prefix-cache workflows.

The translator is an access layer. It does not force any single persistence backend. Object storage, key/value storage, vector indexes, and prompt-prefix cache artifacts are accessed through modular backend adapters. Coherence-CE remains the policy and placement boundary; inference actors do not learn OpenZFS, DPU, NVMe-oF, RoCEv2, RDMA, CXL, or physical-storage topology.

## 2. Non-negotiable constraints

- Python implementation.
- POSIX-compatible runtime model.
- FreeBSD and Linux support.
- No systemd dependency.
- No journald-only logging.
- No Linux-only service lifecycle assumptions.
- Swagger UI available through FastAPI and nginx.
- Prometheus-compatible metrics.
- Prefix-cache exact operations must be ID scoped; keyless collection routes are allowed only for search and predicate invalidation.

## 3. System services

| Service | Port example | Responsibility |
| --- | ---: | --- |
| `s3_net_service` | `8080` | S3-compatible HTTP ingress and S3 response shaping. |
| `meta_translate_service` | `9000` | Command translation, metadata persistence, bidirectional mapping inspection. |
| `rest_net_service` | `8000` | REST API for object, KV, vector, and prompt-prefix-cache operations. |
| `metrics_exporter` | `9100` | Prometheus-compatible metrics aggregation/export. |

## 4. High-level architecture

![S3/Object REST translator architecture](../diagrams/project-coherent-storage_s3-rest-translator.png)

PlantUML source: [`../diagrams/project-coherent-storage_s3-rest-translator.puml`](../diagrams/project-coherent-storage_s3-rest-translator.puml)

## 5. S3 object protocol summary

S3 object protocol is an HTTP object-store interface where the logical object identity is `{bucket}/{key}`. Semantics are conveyed by HTTP method, URI path, query parameters, and headers.

### 5.1 Core S3 operation set

| S3 category | Operations | Translation notes |
| --- | --- | --- |
| Bucket lifecycle | `ListBuckets`, `CreateBucket`, `DeleteBucket`, `HeadBucket` | Maps to `/buckets` and `/buckets/{bucket}`. |
| Object CRUD | `PutObject`, `GetObject`, `HeadObject`, `DeleteObject`, `DeleteObjects` | Maps to `/objects/{bucket}/{key}` and batch delete endpoint. |
| Listing | `ListObjects`, `ListObjectsV2`, `ListObjectVersions` | REST returns JSON; S3 response is rendered as XML where required. |
| Copy | `CopyObject` | S3 header `x-amz-copy-source` maps to JSON copy request. |
| Multipart | `CreateMultipartUpload`, `UploadPart`, `UploadPartCopy`, `ListParts`, `CompleteMultipartUpload`, `AbortMultipartUpload` | REST uses explicit multipart session paths. |
| Tags | `GetObjectTagging`, `PutObjectTagging`, `DeleteObjectTagging` | REST uses JSON tags; S3 uses XML tag set. |
| Metadata | `x-amz-meta-*`, content headers, ETag, length, last modified | Stored as object metadata and projected back to S3 headers. |
| Byte range | `Range` | REST accepts `Range` and returns partial byte stream. |
| Versioning hooks | `versionId` query behavior | Supported where backend adapter implements version state. |

### 5.2 S3 request classification

The translator classifies requests by method, bucket/key shape, query parameters, and S3 headers before constructing a normalized command envelope. The canonical flow is encoded in the PlantUML diagram above and in ADR-022.

## 6. REST API summary

The REST API is the canonical backend contract.

### 6.1 Object endpoints

| Method | Path | Function |
| --- | --- | --- |
| `GET` | `/buckets` | List buckets. |
| `POST` | `/buckets` | Create bucket. |
| `GET` | `/buckets/{bucket}` | List objects. |
| `DELETE` | `/buckets/{bucket}` | Delete empty bucket. |
| `GET` | `/objects/{bucket}/{key}` | Download object. |
| `PUT` | `/objects/{bucket}/{key}` | Upload object. |
| `HEAD` | `/objects/{bucket}/{key}` | Return metadata. |
| `DELETE` | `/objects/{bucket}/{key}` | Delete object. |
| `PUT` | `/objects/{bucket}/{key}/copy` | Copy object. |
| `GET` | `/objects/{bucket}/{key}/tags` | Get object tags. |
| `PUT` | `/objects/{bucket}/{key}/tags` | Set object tags. |
| `DELETE` | `/objects/{bucket}/{key}/tags` | Delete object tags. |

### 6.2 KV and vector endpoints

| Method | Path | Function |
| --- | --- | --- |
| `PUT` | `/kv/{namespace}/{key}` | Store binary or JSON key/value artifact. |
| `GET` | `/kv/{namespace}/{key}` | Retrieve key/value artifact. |
| `DELETE` | `/kv/{namespace}/{key}` | Delete key/value artifact. |
| `POST` | `/vectors/{namespace}` | Upsert vector with metadata. |
| `POST` | `/vectors/{namespace}/search` | Search vector index. |
| `DELETE` | `/vectors/{namespace}/{vector_id}` | Delete vector record. |

### 6.3 Prefix-cache namespace modalities

Prefix-cache routes support the two ADR-023 modalities. Exact artifact operations always include `prefix_id`. Collection search and invalidation are explicit action routes with request bodies.

![Prefix-cache namespace modality decision path](../diagrams/project-coherent-storage_prefix-cache-namespace-modalities.png)

PlantUML source: [`../diagrams/project-coherent-storage_prefix-cache-namespace-modalities.puml`](../diagrams/project-coherent-storage_prefix-cache-namespace-modalities.puml)

#### Unified Namespace routes

| Method | Path | Function |
| --- | --- | --- |
| `PUT` | `/prefix-cache/unified/{namespace}/prefixes/{prefix_id}` | Store prompt-prefix cache artifact in a logical namespace. |
| `GET` | `/prefix-cache/unified/{namespace}/prefixes/{prefix_id}` | Exact prefix-cache lookup. |
| `DELETE` | `/prefix-cache/unified/{namespace}/prefixes/{prefix_id}` | Delete/invalidate one prefix-cache artifact. |
| `POST` | `/prefix-cache/unified/{namespace}/search` | Search namespace for exact or vector-assisted candidates. |
| `POST` | `/prefix-cache/unified/{namespace}/invalidate` | Predicate or epoch-based namespace invalidation. |

#### Dimensional Indexed Namespace routes

| Method | Path | Function |
| --- | --- | --- |
| `PUT` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/prefixes/{prefix_id}` | Store prompt-prefix cache artifact in an indexed locality/compatibility scope. |
| `GET` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/prefixes/{prefix_id}` | Exact prefix-cache lookup inside one declared index. |
| `DELETE` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/prefixes/{prefix_id}` | Delete/invalidate one indexed prefix-cache artifact. |
| `POST` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/search` | Search one declared index with optional authorized escalation. |
| `POST` | `/prefix-cache/dimensional/{namespace}/indexes/{index_id}/invalidate` | Predicate or epoch-based invalidation inside one declared index. |

Compatibility note: `/prefix-cache/{namespace}/{prefix_id}` may be implemented only as an explicitly deprecated alias for Unified Namespace exact operations. It must not be the preferred OpenAPI route for generated clients.

## 7. Bidirectional translation

### 7.1 S3 to REST

A `PUT /bucket/key` request becomes a normalized command envelope, then a REST object or prefix-cache operation. A bucket configured as a prefix-cache bucket can map key segments into `namespace`, `prefix_id`, and optional `index_id` only through an explicit route policy. Ad hoc parsing that guesses physical locality from S3 keys is rejected.

Example normalized command:

```json
{
  "request_id": "req-20260518-000001",
  "direction": "s3_to_rest",
  "s3_operation": "PutObject",
  "rest_operation": "putPrefixCache",
  "method": "PUT",
  "bucket": "llm-prefix-cache",
  "key": "tenant-a/model-x/prefix/sha256-abcd",
  "namespace_mode": "unified",
  "namespace": "tenant-a.model-x",
  "prefix_id": "sha256-abcd",
  "metadata_mode": "minimal"
}
```

### 7.2 REST to S3-shape inspection

REST clients normally write directly to the same backend. When S3-shaped response inspection is needed, clients can use the translation endpoint.

```json
{
  "direction": "rest_to_s3",
  "rest_operation": "putPrefixCache",
  "method": "PUT",
  "path": "/prefix-cache/unified/tenant-a.model-x/prefixes/sha256-abcd",
  "desired_s3_operation": "PutObject"
}
```

## 8. Metadata persistence policy

| Mode | Runtime cost | Use case | Stored fields |
| --- | --- | --- | --- |
| `off` | Lowest | Benchmarking | Metrics counters only. |
| `minimal` | Low | Default production | Request ID, operation, status, latency, bytes, bucket/key digest. |
| `standard` | Moderate | Operational debugging | Minimal fields plus selected headers, caller address, mapping decision, cache hit/miss. |
| `verbose` | High | Lab diagnostics | Full normalized request/response envelopes, payload digests, backend timing. |
| `forensic` | Highest | Controlled fault reproduction | Bounded body capture and full headers with mandatory redaction. |

Required redactions:

- `Authorization`
- `Cookie`
- `Set-Cookie`
- `X-Amz-Security-Token`
- application secrets
- tenant credentials
- raw object payloads unless explicitly enabled

## 9. Prefix-cache design

LLM prompt-prefix caching is modeled as an artifact store with optional vector index sidecar.

Rules:

- Exact prefix-cache operations require `prefix_id`.
- `prefix_id` is derived from canonical model/tokenizer/adapter/runtime identity plus prompt-prefix digest and policy salt.
- Vector search can return a candidate reference only when similarity policy and compatibility checks pass.
- A vector-similar candidate is not automatically safe for KV reuse; model/runtime policy decides whether it can be used, recomputed, or treated as a search hint.
- Invalidation must be scoped by namespace modality, tenant policy, compatibility identity, and optional locality epoch.

## 10. Metrics

Required metrics include:

```text
translator_requests_total{service,operation,status,namespace_mode}
translator_request_latency_seconds_bucket{service,operation,namespace_mode}
translator_bytes_in_total{service,operation}
translator_bytes_out_total{service,operation}
translator_translation_errors_total{direction,operation,error_class}
translator_cache_hits_total{namespace,namespace_mode,index_id,cache_kind}
translator_cache_misses_total{namespace,namespace_mode,index_id,cache_kind}
translator_backend_errors_total{backend,error_class}
translator_metadata_events_total{mode,event_kind}
translator_namespace_escalations_total{namespace,index_id,reason}
```

## 11. Deployment model

### 11.1 Local lab startup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn rest_net_service:app --host 0.0.0.0 --port 8000
uvicorn meta_translate_service:app --host 0.0.0.0 --port 9000
uvicorn s3_net_service:app --host 0.0.0.0 --port 8080
uvicorn metrics_exporter:app --host 0.0.0.0 --port 9100
```

### 11.2 POSIX supervision

Use `supervisord`, `runit`, `s6`, FreeBSD rc scripts, FreeBSD `daemon(8)`, or container entrypoints. Application code must not depend on systemd APIs.

## 12. File map

| Path | Purpose |
| --- | --- |
| `adr/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.md` | ADR record for the translator. |
| `adr/ADR-023_Coherence_CE_Namespace_Modalities.md` | ADR record for Unified and Dimensional Indexed Namespace semantics. |
| `reports/project-coherent-storage_s3-object-rest-api-translator-design.md` | Main design report. |
| `api/s3-object-rest-translator.openapi.yaml` | OpenAPI 3.1 schema for translator REST endpoints. |
| `adr/diagrams/ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator.*` | ADR-specific PlantUML source and renders. |
| `diagrams/project-coherent-storage_s3-rest-translator.*` | Report-level PlantUML source and renders. |
| `diagrams/project-coherent-storage_prefix-cache-namespace-modalities.*` | Namespace modality PlantUML source and renders. |
