# ADR-006: OpenZFS, NVMe-oF, and Media Layout

**Project:** Project Coherent Storage  
**Version:** 2026-Q2  
**Package:** v2 inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Decision summary

Use OpenZFS and NVMe-oF cross-node mirrored NAND as the core durable block-storage foundation, while tuning pool layout, media classes, zvol/dataset use, and replication around inference read latency, write endurance, cache rebuild behavior, and clear separation from active decode KV synchronization.

## Context

OpenZFS provides checksums, snapshots, compression, scrubs, and operationally useful data integrity. The v0 architecture selected OpenZFS-backed storage nodes exporting zvols over NVMe-oF/RDMA and retained DPU/SPDK offload where supported. The earlier v0/v1 text treated cross-node mirrored ZFS vdevs as experimental Mode X; this refresh corrects that disposition to match the coherent-storage requirement: cross-node mirrored ZFS/NVMe-oF is the core NAND block-storage substrate, subject to explicit failure and latency gates. The RAG corpus supports the value of ZFS integrity, but also shows that ML and LLM workloads create many small random reads, cache/prefetch needs, bursty writes, and high sensitivity to storage configuration.

The inference-optimized architecture therefore keeps OpenZFS for durable T2/T3 services while making the hot KV service and RAG/vector indexes explicit consumers above it. The OCP power and AI data-center references add another layout constraint: media density, cache rebuild behavior, and storage-node admission must fit rack power, pulse-load, protection, thermal, power-quality, and backup-energy envelopes.

## Decision

- Use OpenZFS pools on storage and cache nodes as T2 warm-cache and T3 durable tiers, with cross-node mirrored vdevs over NVMe-oF/RDMA as the required coherent NAND block-storage pattern after qualification gates pass.
- Export block namespaces with NVMe-oF/RDMA when the consumer needs block semantics, such as VM disks, local cache volumes, storage-client mounts, and coherent NAND-backed durable inference data classes.
- Use datasets or object/file services for immutable models, corpora, embeddings, indexes, artifacts, and logs unless block access is required; these services may still be backed by the coherent NAND block tier.
- Preserve the distinction between the durable coherent NAND substrate and the active per-token KV/decode path: active decode must not synchronously wait on cross-node mirror operations for every token.
- Select media classes by workload: low-latency/endurance media for metadata and sync-heavy paths, TLC/SLC-class NVMe for hot/warm data, QLC for cold and read-mostly objects, and ZNS only for workloads with qualified append/log layouts.
- Keep ARC, hugepages, SPDK memory, DPU services, and inference runtime memory budgets explicit to avoid cache starvation.
- Bind each storage/cache-node profile to a rack power envelope, PSU/power-shelf profile, thermal class, power-quality assumption, and ESS/backup posture before workload promotion.
- Classify CXL devices before any OpenZFS use: volatile CXL is host memory only; persistent byte-addressable CXL is for PMem-aware services above OpenZFS; block-presented CXL may enter OpenZFS only after power-loss, flush, endurance, latency, replacement, import, and mirroring qualification.

## Media classes

| Media class | Recommended use | Notes |
| --- | --- | --- |
| Low-latency SCM/Optane-like devices where available | SLOG, metadata/special vdev, latency-sensitive write intent, high-value hot metadata | Must be mirrored and monitored; scarcity limits scope. |
| Volatile CXL Type-3 memory expansion | Coherence-CE metadata/cache, KV-D1/KV-D2 warm staging, vector heads, object metadata, ARC/page-cache capacity under explicit budgets | Not durable media; do not use for SLOG, special vdev, or pool storage. Must be CPU/root-complex-local and scheduler-visible. |
| Persistent or block-presented CXL media | PMem-aware services above OpenZFS, or L2ARC/SLOG/special-vdev/pool roles only after block/persistence qualification | Require power-loss protection, flush/fence proof, endurance, mirroring, replacement/import drills, and no hidden switched/bifurcated hot path. |
| High-endurance NVMe | Hot KV spill, vector index shards, model manifest/object metadata, canary namespaces | Prefer for write-heavy or low-tail-latency tiers. |
| Capacity NVMe TLC | Warm KV, model shard cache, hot corpus chunks, zvols | Default T2/T3 workhorse. |
| QLC NVMe | Read-mostly model/corpus replicas, old embeddings, batch artifacts | Keep write amplification and endurance visible. |
| ZNS SSD | Append/log-structured object segments, rebuild queues, corpus ingest experiments | Qualified workload only; client/server zone management must be explicit. |
| HDD/object archive | Cold corpus, retired models, compliance/audit copies | Excluded from online inference hot path. |
| Power-constrained media profile | Any media mix operating near rack or PSU limits | Requires explicit power headroom, pulse-load, thermal, and backup-energy checks. |

## OpenZFS policy

- Enable checksums and regular scrubs for durable pools.
- Use compression by default for metadata, text corpora, logs, and cache data only after measuring CPU, DPU, and QAT acceleration/fallback overhead plus compression ratio.
- Tune dataset recordsize by data class. Small metadata and vector index fragments should not inherit large streaming records.
- Keep model/object/corpus data immutable and snapshot-friendly.
- Use zvols for NVMe-oF exports only when block semantics are required.
- Monitor ARC hit ratio, ARC size, zpool latency histograms, vdev latency, scrub/resilver state, pool fragmentation, and power/thermal state during scrubs and resilvers.
- Do not treat QAT compression or cryptographic acceleration as OpenZFS durability evidence. QAT may accelerate adjacent service compression, TLS/IPsec, or gateway/helper transforms only when payload-size, destination-buffer, VF/PF, reset, and fallback behavior are qualified.

## CXL and OpenZFS policy

- Volatile CXL may increase host memory capacity for ARC/page-cache, Coherence-CE metadata, warm KV staging, vector heads, or storage-service buffers only with explicit NUMA and memory budgets.
- Volatile CXL must never be treated as OpenZFS durable media, SLOG, special vdev, or a basis for durable acknowledgement.
- Persistent byte-addressable CXL or Optane PMem-style memory may be used by PMem-aware services above OpenZFS only after DAX/persistence/fencing validation; OpenZFS byte-addressable semantics are not assumed.
- CXL presented as a block device may be considered for L2ARC, SLOG, special vdev, or pool membership only after power-loss protection, flush ordering, endurance, latency, import, replacement, and mirroring tests pass.
- Latency-sensitive OpenZFS-adjacent use rejects hidden CXL switch layers, oversubscribed fabrics, or auto-bifurcation; same CPU socket/root complex and NUMA locality are preferred, while explicit CXL switch fabrics require separate managed-fabric qualification before any OpenZFS-adjacent role.
- ARC, Coherence-CE, SPDK, DPU, runtime, and CXL allocations must be budgeted together so ZFS caching cannot starve inference memory.

## NVMe-oF policy

- Use NVMe-oF/RDMA for block namespaces requiring low-latency disaggregated access.
- Require dual paths over Fabric A and Fabric B for production lab namespaces.
- Use multipath/ANA where supported and explicit failover tests where not.
- DPU/SPDK target paths are preferred only after telemetry and fallback are validated.
- Initiator and target queue depths must be workload-specific, not copied globally from one benchmark.

## Positive consequences

- ZFS integrity and operations remain in the durable storage foundation.
- Inference hot-path behavior is not forced through a single block abstraction.
- Media endurance and tail-latency risks are visible by workload.
- Coherent NAND block storage becomes a first-class substrate while active inference services can still avoid per-token durability latency.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| ARC competes with inference, SPDK, or hugepages | Pin memory budgets and alert on pressure. |
| QLC endurance is consumed by cache churn | Restrict QLC to read-mostly or cold tiers and monitor writes per namespace. |
| ZNS adds operational complexity | Use only for append/log workloads with explicit zone management and rollback. |
| NVMe-oF failure surprises consumers | Require A/B paths, failure drills, and initiator recovery tests. |
| Cross-node mirror failure semantics are unsafe | Gate coherent NAND promotion on node-loss, fabric-loss, import, checksum, latency regression, and resilver drills. |
| Rebuild, scrub, or cache warmup exceeds power/thermal envelope | Gate heavy storage maintenance with rack power, PSU/power-shelf, ESS, and thermal telemetry. |
| Volatile CXL is mistaken for persistent OpenZFS media | Require device role classification and forbid durable acknowledgements, SLOG, special vdev, or pool membership unless persistence/block semantics are proven. |
| CXL topology adds unpredictable tail latency | Reject hidden switch layers and auto-bifurcated placement for latency-sensitive OpenZFS/Coherence/DPU/GPU roles unless measured and qualified. |
| QAT acceleration changes compression/crypto failure mode | Keep OpenZFS checksum/durability semantics authoritative; require CPU fallback, payload-size guards, endpoint reset drills, and telemetry before using QAT-assisted service paths. |

## Acceptance criteria

- Each pool/dataset/zvol has a declared data class, media class, recordsize policy, replication policy, and SLO class.
- A canary NVMe-oF namespace survives one fabric path failure without corruption.
- ZFS scrub and snapshot jobs run during inference benchmarks without violating storage SLOs.
- ARC, hugepage, SPDK, DPU, and runtime memory budgets are documented for each storage/cache node profile.
- Cross-node mirrored ZFS/NVMe-oF passes node-loss, fabric-loss, import, checksum, latency regression, and resilver gates before serving as the production-like coherent NAND block substrate.
- Active decode/KV tests prove the per-token path remains served from accelerator/host/cache tiers rather than synchronous remote mirror acknowledgement.
- Scrub, resilver, model-cache warmup, and index rebuild tests record rack power, PSU/power-shelf health, thermal state, and storage SLO impact.
- Any OpenZFS-adjacent CXL use records role, persistence class, CPU socket/root complex, slot, NUMA node, link width/speed, switch hop count, bifurcation state, firmware, telemetry endpoint, and failure-domain mapping.
- Any QAT-assisted compression or cryptographic path records QAT device/driver/firmware, PF/VF ownership, trusted-guest policy, payload-size guards, destination-buffer minima for decompression, CPU fallback behavior, and whether a QAT endpoint fault changes scheduler admission.

## Source documents

| ID | Use |
| --- | --- |
| A0, A1, A2 | Existing OpenZFS/NVMe-oF modes and RDMA mirrored ZFS/coherent flash basis for the required NAND block substrate. |
| R04, R21 | ML/HPC I/O patterns, storage hierarchy, burst buffers, PMem, QLC, ZNS. |
| R22 | ZFS configuration sensitivity and HPC I/O optimization context. |
| R23 | ZFS integrity, checksums, compression, and production storage reliability evidence. |
| R24 | ZNS design for write amplification and multi-tenant disaggregated storage. |
| R28, R29, R79, R83, R84, R85, R138 | CXL/PMem/Optane memory and storage-tier context for media classification. |
| R31, R35, R36, R41, R42 | OCP rack/facility power, PSU, HVDC/LVDC, energy-storage, thermal, and power-quality constraints on media and maintenance layout. |
| R33 | DC-SCM/platform management context for storage-node management surfaces. |
| R251 | BMRA hardware/BOM, BIOS, NUMA-aligned storage, Ansible, SR-IOV/IOMMU, QAT, telemetry, and verification guidance. |
| R252 | QAT crypto/compression acceleration limits, virtualized VF/PF behavior, endpoint/reset risk, and buffer-size constraints. |
| O10, O11, O12, O13 | Official CXL and Optane references for CXL-vs-Optane comparison and topology-governed memory expansion. |
| ADR-015 | Governs CXL roles, placement, OpenZFS interaction, and Optane PMem comparison. |
