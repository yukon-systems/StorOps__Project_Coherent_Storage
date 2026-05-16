# ADR-008: RAG Vector Index and Corpus Service

**Project:** Project Coherent Storage  
**Version:** 2026-Q2  
**Package:** v2 inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Make RAG corpus, embedding, vector-index, retrieval-result, and chunk-hydration storage first-class services. Store source chunks and derived indexes as immutable versioned artifacts, keep hot index heads and high-value shards close to inference workers, and gate production use on both latency and recall quality.

## Context

The v0 architecture centered on coherent flash and general AI/HPC storage. The inference workload adds a retrieval path that can dominate TTFT when queries require embedding, vector search, reranking, and chunk hydration before decode. The RAG corpus is therefore not a side dataset. It is part of the online inference path and must be versioned, cached, measured, and scheduled like model data.

The RAG corpus also has a different correctness model than KV cache. KV cache is recomputable and tied to a runtime sequence. Corpus chunks, embeddings, and vector indexes are durable derived artifacts that must remain reproducible and version-compatible. The 2026 refresh also treats the local RAG source set itself as a managed corpus: extraction status, failed documents, source IDs, and impact classification are part of reproducibility evidence.

## Decision

- Store corpus chunks as immutable, content-addressed objects with versioned manifests.
- Store embeddings and vector indexes as immutable derived artifacts tied to corpus version, embedding model, tokenizer/chunker, index algorithm, quantization policy, and build ID.
- Keep hot vector-index heads, shard routing metadata, and high-value posting/index data in T1/T2.
- Store full index shards and corpus chunks in T2/T3 with replicated local hot subsets near inference workers.
- Cache query embeddings and retrieval result sets only when the cache key includes all semantic compatibility fields.
- Treat index builds, re-indexing, and corpus ingest as background/proactive workloads that cannot starve interactive inference.
- Require recall-quality gates in addition to latency gates before a vector index is promoted.
- Require corpus-build manifests to record extraction status, failed/omitted sources, source IDs, and source-to-ADR or source-to-product impact classification when the corpus drives architecture decisions.

## Data model

| Object | Required identity fields |
| --- | --- |
| Corpus chunk | `corpus_id`, `corpus_version`, `source_hash`, `source_id`, `extraction_status`, `chunker_id`, `chunk_id`, `acl_policy`, `retention_policy` |
| Embedding vector | `corpus_version`, `chunk_id`, `embedding_model`, `embedding_model_version`, `embedding_dimensions`, `normalization`, `build_id` |
| Vector index shard | `corpus_version`, `embedding_model_version`, `index_algorithm`, `index_params`, `quantization_policy`, `shard_id`, `build_id` |
| Retrieval result cache | `query_hash`, `embedding_model_version`, `corpus_version`, `index_build_id`, `acl_scope`, `reranker_version`, `top_k`, `score_policy` |
| Hydrated chunk cache | `chunk_id`, `corpus_version`, `format`, `compression`, `acl_scope` |

## Retrieval path

1. Validate tenant, corpus, ACL, and model compatibility.
2. Normalize and embed the query using a versioned embedding service.
3. Route the vector search to local or low-latency replicated shards.
4. Fetch candidate chunk IDs and scores from the index service.
5. Apply optional reranking with a versioned reranker.
6. Hydrate selected corpus chunks from T1/T2/T3.
7. Pass retrieved context to the inference runtime with corpus and index version metadata.
8. Record retrieval latency, recall-quality sample state, shard fanout, and chunk-hydration latency.

## Storage and placement policy

- T1 memory holds shard routing tables, hot index heads, small high-reuse indexes, and retrieval-result metadata.
- T2 local NVMe/OpenZFS holds hot index shards, hot corpus chunks, embedding shards, and hydrated chunk cache.
- T3 RDMA object or file tiers hold durable corpus objects, full embeddings, full indexes, and build artifacts.
- T4 archive holds retired corpus versions and reproducibility evidence.
- Query embedding cache and retrieval-result cache are recomputable and may be evicted aggressively.
- Corpus chunks, embeddings, and index builds are durable artifacts and must survive cache node loss.

## Quantization and compression policy

- Vector quantization is allowed for index memory reduction and throughput only after recall-quality gates pass.
- KV-cache quantization and vector-index quantization must be configured independently.
- Compression is allowed for corpus chunks and hydrated context caches when CPU/DPU overhead does not violate TTFT.
- Quantized index versions must be separately identified and reproducible from source embeddings.

## Consistency and security

- Retrieval must never mix incompatible corpus, embedding, index, reranker, or ACL versions.
- ACL filtering must occur before returning chunk content to the inference runtime.
- Cache keys must include tenant/ACL scope or an equivalent non-bypassable authorization domain.
- Index promotion is an atomic manifest update. Incomplete builds cannot be queried by production traffic.
- Failed or reference-only extractions remain in the corpus manifest with explicit status; they cannot be silently treated as reviewed text evidence.
- Corpus deletion, legal hold, and retention policies must flow into chunk, embedding, index, and cache invalidation.

## Positive consequences

- RAG latency becomes visible and schedulable.
- Corpus and index reproducibility improves auditability and rollback.
- Vector memory pressure can be managed without corrupting semantic compatibility.
- Interactive inference is protected from background ingest and re-index work.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Vector quantization reduces answer quality | Promote quantized indexes only after recall and task-quality gates pass. |
| Corpus/index version drift causes wrong-context answers | Use immutable manifests and compatibility fields in every cache key. |
| Hot index replicas consume too much T1/T2 capacity | Rank replicas by query heat, tenant priority, and SLO class. |
| ACL caching creates data exposure | Include ACL scope in cache identity and test denial paths before rollout. |
| Architecture decisions are made from an incomplete corpus | Require extraction coverage and source-impact ledgers before promoting RAG-derived architecture updates. |

## Acceptance criteria

- A corpus manifest can reproduce chunk, embedding, and vector-index identity for any production retrieval result.
- A retrieval request returns the corpus version, embedding model version, index build ID, and reranker version used.
- A stale or incompatible retrieval-result cache entry is rejected by key validation.
- A quantized index candidate passes configured recall-quality and latency gates before promotion.
- Re-indexing under load cannot violate interactive KV/model SLOs.
- Dashboard panels show embedding latency, vector-search latency, chunk-hydration latency, recall sample status, shard fanout, and cache hit rate.
- A corpus build report accounts for every source file as extracted, native text, image-only, binary/reference, or failed, and blocks promotion on undocumented omissions.

## Source documents

| ID | Use |
| --- | --- |
| A0 | Existing governance, SLO, and automation baseline. |
| R03 | RAG pipeline, embedding service, and HPC LLM serving context. |
| R04 | ML I/O caching, prefetching, and small random-read pressure. |
| R05 | RDMA-first object service pattern for data-plane delivery. |
| R21 | HPC storage hierarchy and memory/storage tiering direction. |
| R27 | Online vector quantization direction for vector database and RAG workloads. |
| R28 | Disaggregated memory hierarchy and runtime management context. |
| R31-R43 | 2026-05-13 local corpus refresh inputs and extraction/accounting requirements for RAG-derived architecture updates. |

