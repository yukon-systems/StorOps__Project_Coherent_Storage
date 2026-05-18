#!/usr/bin/env python3
"""Generate per-ADR PlantUML architecture workflow diagrams.

The diagrams are intentionally repo-relative and version-neutral. They model
engineering build direction: actor boundary, decision points, data/resource
flow, protocol planes, memory buffers, network classes, and telemetry gates.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "adr" / "diagrams"

COMMON_HEADER = """@startuml
!theme plain
skinparam shadowing false
skinparam roundcorner 12
skinparam defaultFontName DejaVu Sans
skinparam ArrowColor #34495E
skinparam activity {
  BackgroundColor #FDFEFE
  BorderColor #566573
  DiamondBackgroundColor #FCF3CF
  DiamondBorderColor #B7950B
  StartColor #145A32
  EndColor #922B21
}
skinparam note {
  BackgroundColor #FEF9E7
  BorderColor #B7950B
}
"""

COMMON_LEGEND = """
legend right
Design defaults for diagrams unless an ADR narrows them:
- Actor/API: HTTPS 443 or 8443; OpenAI-compatible API plus Coherence-native API.
- RoCEv2: UDP destination 4791; jumbo MTU 9000; PFC only on RDMA priorities.
- NVMe-oF: discovery/controller service on TCP/RDMA port 4420; DPU-mediated targets.
- Telemetry: OTLP gRPC 4317, OTLP HTTP 4318, Prometheus 9090/9100, gNMI 9339.
- Timing: PTP event/general UDP 319/320 on an isolated timing/management class.
- VLAN plan: site-specific IDs are allowed, but classes must stay isolated:
  mgmt/OOB, frontend/API, RDMA rail-A, RDMA rail-B, storage/NVMe-oF, telemetry, timing.
- Trunks: 802.1Q tagged uplinks; rail-A and rail-B must not share a failure domain.
- Buffers: kv_hbm_active, kv_dram_warm, kv_cxl_warm, kv_rdma_staging,
  zfs_slog, zfs_arc, zfs_l2arc, object_cache, vector_head_cache.
endlegend
"""


def diagram(title: str, body: str) -> str:
    return f"{COMMON_HEADER}title {title}\n{COMMON_LEGEND}\n{body.strip()}\n@enduml\n"

DIAGRAMS: dict[str, str] = {
"ADR-001_Inference_Storage_Principles_and_SLOs": diagram("ADR-001 - Inference SLO Contract and Storage Admission", r'''
start
partition "Actor boundary" {
  :Client submits inference request\nOpenAI-compatible HTTPS 443\nor Coherence-native HTTPS 8443;
  :Attach tenant_id, model_id, adapter_id,\nslo_class, privacy_domain, trace_id;
}
partition "Coherence-CE policy" {
  if (SLO class declared and authorized?) then (yes)
    :Map request to TTFT/TPOT,\nKV residency, retrieval, and durability budget;
  else (no)
    :Use conservative default profile\nor reject policy-unsafe request;
  endif
  if (Hot path requires storage knowledge by actor?) then (yes)
    :Reject contract: actors never bind\nto OpenZFS, DPU, RoCEv2, CXL, or UA-Link;
    stop
  else (no)
    :Keep lower layers behind Coherence-CE;
  endif
}
partition "Resource placement" {
  if (kv_hbm_active and model resident?) then (hot)
    :Admit to local accelerator path\nHBM/DRAM, same NUMA/root complex;
  else (warm/cold)
    :Plan warm hydration from kv_dram_warm,\nkv_cxl_warm, object_cache, or OpenZFS substrate;
  endif
}
partition "Admission outcome" {
  if (all budgets have fresh telemetry?) then (GREEN/AMBER)
    :Return admission lease + deadline budget\nwithout leaking topology identifiers;
  else (RED/DRAIN)
    :Throttle, queue, move model, or fail fast\nwith retryable Coherence error;
  endif
}
stop
'''),
"ADR-002_Hot_KV_and_Prefix_Cache_Data_Plane": diagram("ADR-002 - Hot KV and Prefix Cache Data Plane", r'''
start
partition "Inference actor" {
  :vLLM adapter computes prefix_key\nmodel_hash, tokenizer_hash, tenant, seq_range;
  :POST /coherence/kv/lookup\nHTTPS 8443; actor sees handles only;
}
partition "Coherence-CE mesh" {
  if (prefix hit in kv_hbm_active?) then (hit)
    :Return GPU-local descriptor\nHBM page table alias, no storage path;
  else (miss)
    if (hit in kv_dram_warm or kv_cxl_warm?) then (warm hit)
      :Schedule DMA/RDMA hydration\nkv_rdma_staging -> kv_hbm_active;
    else (cold miss)
      :Select recompute or durable fetch\nfrom object_cache/OpenZFS via DPU;
    endif
  endif
}
partition "Memory and fabric movement" {
  if (remote hydration required?) then (yes)
    :Use RoCEv2 UDP 4791 on rail-A/rail-B\nDSCP/PFC priority for RDMA only;
    :Stage into kv_rdma_staging\npinned host/GPU memory registration;
  else (no)
    :Stay on local PCIe/CXL/UA-Link path;
  endif
}
partition "Write/update policy" {
  if (KV class >= KV-D2?) then (durable)
    :Publish idempotent object with epoch\nflush policy to DPU/OpenZFS path;
  else (recomputable)
    :Record eviction and recompute hints only;
  endif
}
stop
'''),
"ADR-003_Model_Weight_Object_and_Corpus_Data_Tiers": diagram("ADR-003 - Model Weight, Object, and Corpus Tiering", r'''
start
partition "Request classification" {
  :Resolve model_id, adapter_id, corpus_id,\nembedding_profile, tokenizer_version;
  if (model weights resident in GPU/host cache?) then (resident)
    :Use model_resident_token + checksum proof;
  else (cold)
    :Plan model hydration from object tier\nHTTPS/S3 443 or RDMA object path;
  endif
}
partition "Tier selector" {
  if (artifact is mutable runtime KV?) then (KV)
    :Route to Coherence KV classes\nkv_hbm_active/kv_dram_warm/kv_cxl_warm;
  elseif (artifact is immutable model/corpus?) then (object)
    :Route to object_cache + OpenZFS snapshots\ncontent address + manifest checksum;
  else (metadata)
    :Route to metadata store\nstrong consistency + audit log;
  endif
}
partition "Storage substrate" {
  :DPU presents NVMe-oF namespaces\nport 4420 over storage VLAN/rail;
  :OpenZFS validates checksum, compression,\nsnapshot, ARC/L2ARC behavior;
  if (bulk transfer risks inference SLO?) then (yes)
    :Rate-limit background prefetch\nseparate traffic class and queue;
  else (no)
    :Permit read-ahead and cache warming;
  endif
}
partition "Telemetry" {
  :Emit cache-hit, hydration-bytes, checksum,\np99 object-read and corpus-read metrics;
}
stop
'''),
"ADR-004_RDMA_Fabric_and_GPU_Direct_Data_Paths": diagram("ADR-004 - RDMA Fabric and GPU-Direct Data Paths", r'''
start
partition "Path selection" {
  :Classify data move: KV hydration, model load,\nobject fetch, collective, or storage IO;
  if (same accelerator island?) then (scale-up)
    :Use local PCIe/UA-Link/NVLink-class path\nno routable IP storage exposure;
  else (scale-out)
    :Select RoCEv2 rail-A or rail-B\nUDP 4791, ECMP hash, DSCP, PFC priority;
  endif
}
partition "Registration and buffers" {
  if (GPU-direct supported and qualified?) then (yes)
    :Register GPU pages for RDMA\nkv_hbm_active <-> kv_rdma_staging;
  else (fallback)
    :Use pinned host bounce buffer\nkv_dram_warm with explicit copy budget;
  endif
  if (MR/QP ownership crosses tenant boundary?) then (unsafe)
    :Fence memory region and reject placement;
    stop
  endif
}
partition "Lossless Ethernet controls" {
  :Validate MTU 9000, PFC headroom, ECN/DCQCN,\nqueue mapping, cable/FEC, trunk member health;
  if (pause storm, ECN drift, or stale counters?) then (degrade)
    :Demote rail to AMBER/RED and reroute\nwithout actor-visible topology leakage;
  else (healthy)
    :Admit RDMA flow with lease TTL;
  endif
}
partition "Observability" {
  :Export per-rail p50/p99 latency, retransmit,\nPFC pause, ECN mark, QP error, GPU copy time;
}
stop
'''),
"ADR-005_DPU_and_SmartNIC_Offload_Boundaries": diagram("ADR-005 - Mandatory DPU/SmartNIC Offload Boundary", r'''
start
partition "Host and DPU inventory" {
  :Discover DPU PCIe/root-complex locality,\nNIC ports, NVMe namespaces, crypto, telemetry;
  if (storage path lacks qualified DPU?) then (not compliant)
    :Mark host storage path RED\nhost fallback allowed only for degraded drills;
    stop
  else (qualified)
    :Bind NVMe-oF, RDMA MR/QP mediation,\ntenant isolation, and telemetry to DPU profile;
  endif
}
partition "Data path" {
  :Coherence durable IO request\n-> DPU queue pair and namespace policy;
  :DPU terminates/mediates NVMe-oF\nport 4420 and RoCEv2 UDP 4791;
  if (operation is small synchronous write?) then (write)
    :Apply idempotency key, ordering epoch,\noptional crypto/compression offload;
  else (read/bulk)
    :Use read steering and DMA to host/GPU staging;
  endif
}
partition "Control and isolation" {
  if (DPU telemetry stale or firmware drift?) then (unsafe)
    :Drain namespace, revoke MRs, fence QPs,\nmove admission to AMBER/RED;
  else (safe)
    :Expose only Coherence metrics to scheduler;
  endif
}
partition "Fallback" {
  :Host stack fallback requires explicit operator mode,\naudit event, rate limit, and rollback gate;
}
stop
'''),
"ADR-006_OpenZFS_NVMe_oF_and_Media_Layout": diagram("ADR-006 - OpenZFS NVMe-oF and Media Layout", r'''
start
partition "Namespace and pool design" {
  :Create mirrored NAND vdev sets\nacross independent storage nodes/rails;
  :Expose zvol/object backing through DPU\nNVMe-oF port 4420 on storage VLAN;
  if (mirror legs share rack, PSU, switch, or rail?) then (invalid)
    :Reject layout; failure domains are not independent;
    stop
  endif
}
partition "Write path" {
  :Coherence durable object -> DPU -> NVMe-oF -> OpenZFS;
  if (sync/durable class?) then (sync)
    :Commit via zfs_slog and checksum tree\nbefore durable ACK;
  else (async/recomputable)
    :Buffer under write-back policy\nwith flush deadline and loss budget;
  endif
}
partition "Read path" {
  if (hit in zfs_arc or zfs_l2arc?) then (cache hit)
    :Serve to object_cache or kv_rdma_staging;
  else (media)
    :Read NAND mirror, verify checksum,\nrepair from good replica if needed;
  endif
}
partition "Operations" {
  if (resilver/scrub/degraded mirror active?) then (degraded)
    :Lower admission, reserve rail bandwidth,\nblock hot inference placement if p99 rises;
  else (normal)
    :Permit scheduled scrubs and snapshot replication;
  endif
}
stop
'''),
"ADR-007_Inference_Scheduler_Locality_and_Admission_Control": diagram("ADR-007 - Scheduler Locality and Admission Control", r'''
start
partition "Admission request" {
  :Scheduler receives model_id, tenant, batch shape,\ncontext length, KV growth estimate, SLO class;
  :Query Coherence admission summary\nHTTPS 8443 / telemetry snapshot TTL;
}
partition "Locality matrix" {
  if (model and tokenizer resident?) then (resident)
    :Score GPU/host by HBM, DRAM, NUMA,\nroot complex, UA-Link island;
  else (cold)
    :Add model hydration cost and object tier pressure;
  endif
  if (prefix/KV warm in same pod?) then (local)
    :Prefer same pod, same rail, same CXL pool epoch;
  else (remote)
    :Add RDMA hydration p99 and rail contention cost;
  endif
}
partition "Network and storage gates" {
  if (rail, DPU, CXL, or OpenZFS telemetry stale?) then (unsafe)
    :Mark candidate RED/DRAIN\nno placement on stale evidence;
  else (fresh)
    :Evaluate VLAN/TC isolation, PFC/ECN health,\nDPU queue depth, zpool state;
  endif
}
partition "Decision" {
  if (all budgets fit?) then (GREEN)
    :Issue admission lease with placement vector\nno lower-layer identifiers exposed to actor;
  elseif (fits with throttling?) then (AMBER)
    :Queue, cap batch, or prewarm before admit;
  else (RED)
    :Reject/retry with alternate model or pod;
  endif
}
stop
'''),
"ADR-008_RAG_Vector_Index_and_Corpus_Service": diagram("ADR-008 - RAG Vector Index and Corpus Service", r'''
start
partition "Query ingress" {
  :Inference request requires retrieval\ntrace_id, corpus_id, embedding_profile;
  :Call corpus service through Coherence boundary\nHTTPS 443/8443;
}
partition "Embedding and index path" {
  if (embedding cached?) then (hit)
    :Use embedding_cache and vector_head_cache;
  else (miss)
    :Run embedding model under scheduler SLO budget;
  endif
  if (vector shard local to pod?) then (local)
    :Search local DRAM/CXL index heads;
  else (remote)
    :Fetch shard over RoCEv2/object path\nseparate retrieval traffic class;
  endif
}
partition "Corpus hydration" {
  :Resolve chunk manifest and immutable checksum;
  if (chunk in object_cache/zfs_arc?) then (cache hit)
    :Return chunk bundle to prompt builder;
  else (cold)
    :Read from OpenZFS/object tier via DPU\nNVMe-oF 4420 or HTTPS/S3 443;
  endif
}
partition "Admission feedback" {
  if (retrieval p99 threatens TTFT?) then (degrade)
    :Reduce top_k, rerank budget, or defer request;
  else (ok)
    :Continue prompt assembly and decode;
  endif
}
stop
'''),
"ADR-009_Observability_Benchmarking_and_Rollout_Gates": diagram("ADR-009 - Observability, Benchmarking, and Rollout Gates", r'''
start
partition "Metric ingestion" {
  :Collect Coherence, scheduler, GPU, DPU, CXL,\nRDMA switch, OpenZFS, and corpus metrics;
  :Transport OTLP 4317/4318, Prometheus 9090/9100,\ngNMI 9339, PTP 319/320 timing evidence;
}
partition "Benchmark harness" {
  :Run TTFT/TPOT, KV hit/miss, model cold load,\nRAG retrieval, RDMA incast, zpool degradation tests;
  if (test isolates one failure domain?) then (valid)
    :Record baseline, delta, and rollback threshold;
  else (invalid)
    :Reject noisy benchmark evidence;
  endif
}
partition "Rollout gate" {
  if (p95/p99, error budget, and failure drills pass?) then (pass)
    :Advance canary scope: node -> rack -> pod -> fleet;
  elseif (recoverable with AMBER controls?) then (hold)
    :Cap admission and continue observation;
  else (fail)
    :Rollback, freeze promotion, require RCA;
  endif
}
partition "Evidence retention" {
  :Store relative artifact links, manifest checksums,\nconfiguration snapshots, and decision notes;
}
stop
'''),
"ADR-010_Coherence_CE_Write_Policy_to_OpenZFS": diagram("ADR-010 - Coherence-CE Write Policy to OpenZFS", r'''
start
partition "Write classification" {
  :Publish KV/object mutation with durability class,\nlease_epoch, idempotency_key, byte_count;
  if (class is KV-D0/KV-D1?) then (recomputable)
    :Use write-around or memory-only write-back\nno durable ACK promised;
  elseif (class is KV-D2/KV-D3?) then (bounded loss)
    :Use write-back with flush deadline\nand scheduler-visible dirty-byte budget;
  else (durable)
    :Use write-through to OpenZFS before ACK;
  endif
}
partition "Buffering" {
  :Stage in kv_dram_warm or kv_cxl_warm\ntrack dirty_ranges and writer_epoch;
  if (dirty budget exceeded?) then (yes)
    :Force flush, throttle producer, or demote admission;
  else (no)
    :Continue coalescing and checksumming;
  endif
}
partition "Durable path" {
  :Flush via DPU NVMe-oF port 4420\nRoCEv2 UDP 4791 storage class;
  :OpenZFS commits zfs_slog, checksum, mirror write;
  if (ACK mismatch, timeout, or split brain?) then (failure)
    :Fence writer epoch and trigger recovery semantics;
  else (success)
    :Return durable_epoch to Coherence mesh;
  endif
}
stop
'''),
"ADR-011_KV_Durability_Classes": diagram("ADR-011 - KV Durability Classes and Recovery Contracts", r'''
start
partition "Class assignment" {
  :Classify KV block by recompute cost, privacy,\nreuse probability, active session, and correctness need;
  if (ephemeral token state?) then (KV-D0)
    :Store only in kv_hbm_active\nloss = recompute/abort decode;
  elseif (warm reusable prefix?) then (KV-D1/D2)
    :Use kv_dram_warm or kv_cxl_warm\noptional write-back deadline;
  else (checkpoint/audit critical)
    :Require KV-D3/D4/D5 durable path\nOpenZFS-backed ACK;
  endif
}
partition "Placement matrix" {
  :Map class to allowed buffers, replication count,\nflush interval, encryption, and eviction policy;
  if (class requires cross-node survival?) then (yes)
    :Require DPU/OpenZFS mirror health\nand independent rail availability;
  else (no)
    :Permit local-only eviction under pressure;
  endif
}
partition "Failure behavior" {
  if (node, CXL pool, or rail fails?) then (failure)
    :Apply class-specific recovery: recompute,\nrehydrate, fail session, or restore checkpoint;
  else (normal)
    :Expose class occupancy to scheduler;
  endif
}
stop
'''),
"ADR-012_Coherence_CE_vLLM_Adapter_API_Contract": diagram("ADR-012 - Coherence-CE API Contract for vLLM Adapters", r'''
start
partition "Client-facing API" {
  :Client calls /chat/completions or /responses\nHTTPS 443 using OpenAI-compatible payloads;
  :vLLM adapter may call /coherence/kv/*\nHTTPS 8443 for lookup/publish/reserve/flush;
}
partition "Contract firewall" {
  if (adapter request references DPU, zvol, QP, VLAN, or CXL device?) then (invalid)
    :Reject lower-layer leakage with 4xx contract error;
    stop
  else (valid)
    :Accept logical handles: model_id, prefix_key,\ndurability_class, locality_hint, trace_id;
  endif
}
partition "Operation dispatch" {
  if (lookup?) then (read)
    :Return hit/miss + opaque payload_ref\nno physical address or namespace;
  elseif (publish/flush?) then (write)
    :Return accepted/durable_epoch\naccording to class policy;
  else (admission/health)
    :Return GREEN/AMBER/RED/DRAIN summary;
  endif
}
partition "Streaming behavior" {
  :Preserve token streaming semantics;\nCoherence errors map to retryable, throttled, or fatal classes;
}
stop
'''),
"ADR-013_Failure_Semantics_and_Fencing": diagram("ADR-013 - Failure Semantics and Fencing", r'''
start
partition "Detector" {
  :Observe heartbeat, PTP skew, switch counters,\nDPU health, CXL poison, zpool state, API errors;
  if (signal is stale or conflicting?) then (uncertain)
    :Enter AMBER; reduce admission and collect quorum evidence;
  else (confirmed)
    :Classify node, rail, DPU, CXL, storage, or API failure;
  endif
}
partition "Fence decision" {
  if (writer epoch or RDMA MR may be unsafe?) then (fence)
    :Revoke leases, QPs, memory regions,\nNVMe namespace access, and CXL pool ownership;
  else (drain)
    :Drain sessions and avoid new placement;
  endif
}
partition "Recovery path" {
  if (KV class is recomputable?) then (recompute)
    :Drop volatile buffers and reschedule;
  elseif (durable checkpoint exists?) then (restore)
    :Rehydrate via DPU/OpenZFS mirror path;
  else (fail)
    :Return bounded failure to adapter\nwith correlation and retry policy;
  endif
}
partition "Post-recovery gate" {
  :Require clean telemetry window, latency budget,\nand failure drill evidence before GREEN;
}
stop
'''),
"ADR-014_Coherence_Metrics_Scheduler_Admission": diagram("ADR-014 - Coherence Metrics Rollup to Scheduler Admission", r'''
start
partition "Metric sources" {
  :Collect kv_hit_rate, dirty_bytes, flush_age,\nHBM/DRAM/CXL pressure, DPU queue depth;
  :Collect RoCE p99, ECN/PFC, zpool state,\nmodel residency, corpus retrieval latency;
}
partition "Rollup pipeline" {
  if (metric timestamp beyond TTL?) then (stale)
    :Mark source stale; do not infer health from silence;
  else (fresh)
    :Normalize by tenant, model, pod, rail,\nKV class, and locality domain;
  endif
  :Compute admission vector GREEN/AMBER/RED/DRAIN\nwith reason codes and rollback hint;
}
partition "Scheduler decision" {
  if (GREEN?) then (admit)
    :Place request with lease and SLO budget;
  elseif (AMBER?) then (conditional)
    :Cap batch, prewarm, select alternate rail,\nor queue behind flush;
  else (RED/DRAIN)
    :Reject, migrate, or drain host/pod;
  endif
}
partition "Audit" {
  :Persist decision inputs and trace_id\nfor RCA and reproducible benchmark comparison;
}
stop
'''),
"ADR-015_CXL_Memory_Tiering_and_OpenZFS_Interaction": diagram("ADR-015 - CXL Memory Tiering and OpenZFS Interaction", r'''
start
partition "Tier classification" {
  :Classify object as active decode, warm prefix,\nmetadata/index head, durable checkpoint, or bulk artifact;
  if (active per-token decode?) then (hot)
    :Require HBM/local DRAM; CXL is not the critical path;
  elseif (warm/reusable and latency tolerant?) then (warm)
    :Candidate for kv_cxl_warm or vector_head_cache;
  else (durable/bulk)
    :Route to OpenZFS/object substrate;
  endif
}
partition "CXL admission" {
  if (root-complex, NUMA, switch depth, and RAS qualified?) then (qualified)
    :Assign CXL pool ownership epoch\ntrack bandwidth, p99 latency, poison, thermal state;
  else (reject)
    :Do not place latency-sensitive state on CXL;
    stop
  endif
}
partition "OpenZFS boundary" {
  if (persistence required for correctness?) then (yes)
    :Flush to DPU/OpenZFS durable path\nCXL cannot be the durable ACK by itself;
  else (no)
    :Permit volatile CXL as expansion/cache tier;
  endif
}
partition "Telemetry" {
  :Expose CXL pool pressure and error state\nto Coherence and scheduler only;
}
stop
'''),
"ADR-016_Roadmap_Evidence_and_Public_Claim_Guardrails": diagram("ADR-016 - Roadmap Evidence and Public Claim Guardrails", r'''
start
partition "Source intake" {
  :Ingest vendor brief, standard, Linux doc, paper,\nrepo snapshot, benchmark, or partner announcement;
  if (source is primary and archived?) then (strong)
    :Grade direct evidence with URL, checksum, date, scope;
  else (weak)
    :Grade as adjacent, inference, negative-control,\nor unverified; do not promote to claim;
  endif
}
partition "Claim construction" {
  if (claim names a vendor/product/partnership?) then (strict)
    :Require direct source that states that exact relationship;
  else (architecture inference)
    :Label recommendation separately from fact;
  endif
}
partition "Publication gate" {
  if (evidence grade supports public statement?) then (publish)
    :Include citation, date, and residual risk;
  else (hold)
    :Move to research backlog or appendix guardrail;
  endif
}
partition "Audit" {
  :Keep relative archive path and extraction status;\nno host-specific filesystem paths in public docs;
}
stop
'''),
"ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow": diagram("ADR-017 - Research Metadata and arXiv Publication Workflow", r'''
start
partition "Metadata acquisition" {
  :Query arXiv API or S3 bulk metadata\nwith requester-pays credentials outside docs;
  if (rate limit or credential unavailable?) then (fallback)
    :Record failure mode and use local archived PDFs\nwithout fabricating metadata;
  else (success)
    :Store title, authors, DOI/arXiv ID, date,\nlicense, checksum, and relative archive path;
  endif
}
partition "Corpus processing" {
  :Extract PDF text to processing cache;\nchunk, embed, and index for RAG;
  if (text extraction fails?) then (failure)
    :Record filename and parser error;\ndo not silently omit;
  endif
}
partition "Publication package" {
  :Generate Markdown, LaTeX, BibTeX, figures,\nand source archive with relative links;
  if (TeX builds locally?) then (build)
    :Attach PDF and log evidence;
  else (no toolchain)
    :Record not-tested TeX build gap;
  endif
}
partition "Review" {
  :Run citation, path, and claim-grade checks\nbefore external submission;
}
stop
'''),
"ADR-018_UALink_Pod_Scale_Fabric_and_Compute_Domains": diagram("ADR-018 - UA-Link Pod-Scale Fabric and Compute Domains", r'''
start
partition "Pod topology" {
  :Inventory accelerator nodes, UA-Link switches,\nPCIe root complexes, GPU memory, NICs, DPUs;
  if (compute domain has mixed unqualified accelerators?) then (unsafe)
    :Separate into capability pools until collective profile passes;
  else (qualified)
    :Create pod-local scale-up domain;
  endif
}
partition "Traffic separation" {
  :UA-Link handles accelerator scale-up traffic\ninside pod boundary;
  :RoCEv2/Ethernet handles scale-out, storage,\nmanagement, telemetry, and frontend traffic;
  if (storage traffic attempts UA-Link path?) then (invalid)
    :Reject design; storage remains DPU/RDMA/OpenZFS path;
  endif
}
partition "Scheduler locality" {
  if (KV/model/collective fits same pod?) then (local)
    :Prefer same UA-Link island and same rail affinity;
  else (remote)
    :Account for RoCE hydration and cross-pod latency;
  endif
}
partition "Admission gate" {
  :Expose only pod locality, capability profile,\nand health state to Coherence/scheduler;
}
stop
'''),
"ADR-019_Pod_Scale_Network_Architecture_and_RDMA_RoCEv2_Tuning": diagram("ADR-019 - Pod-Scale Network Planes and RoCEv2 Tuning", r'''
start
partition "Plane design" {
  :Define isolated classes: mgmt/OOB, frontend/API,\nRDMA rail-A, RDMA rail-B, storage/NVMe-oF, telemetry, timing;
  :Use 802.1Q trunks with explicit allowed VLANs;\nno native untagged data VLAN on fabric trunks;
  if (rail-A and rail-B share switch ASIC, PSU, or trunk?) then (invalid)
    :Reject bandwidth/failover design; rails are not independent;
    stop
  endif
}
partition "RoCEv2 tuning" {
  :Map RDMA priority to PFC only where needed;\nset ECN/DCQCN thresholds and headroom by port speed;
  :Validate MTU 9000, FEC, ECMP hashing,\nflowlet/packet spray only if qualified;
  if (PFC pause storm or ECN mismatch observed?) then (degrade)
    :Mark rail AMBER/RED, lower admission,\nreroute non-critical flows;
  else (healthy)
    :Admit RoCEv2 UDP 4791 flows;
  endif
}
partition "Storage network" {
  :NVMe-oF uses DPU-mediated port 4420\nseparate storage class and queue budget;
  if (storage and inference collectives contend?) then (yes)
    :Throttle background storage/prewarm\nor move to alternate rail;
  endif
}
partition "Telemetry" {
  :Export per-port p99 latency, queue depth, drops,\nPFC, ECN, QP errors, trunk member health;
}
stop
'''),
"ADR-020_CXL_Memory_Pools_for_UALink_Pods": diagram("ADR-020 - CXL Memory Pools for Pod-Scale Systems", r'''
start
partition "Pool discovery" {
  :Discover CXL type, capacity, switch/fabric manager,\nroot-complex distance, RAS, poison, thermal state;
  if (device is behind hidden switch layers\nor auto-bifurcated unknown topology?) then (reject)
    :Reject latency-sensitive placement; require explicit topology;
    stop
  endif
}
partition "Ownership and allocation" {
  :CXL pool manager grants ownership_epoch\nto Coherence-CE, not to inference actor;
  if (pool is same pod/root-complex as target GPU?) then (preferred)
    :Allocate kv_cxl_warm/vector_head_cache\nwith NUMA-aware latency budget;
  else (remote)
    :Use only for lower-priority warm state\nor reject for SLO-bound path;
  endif
}
partition "Data flow" {
  :Coherence moves warm KV: kv_dram_warm <-> kv_cxl_warm\nthen hydrates kv_hbm_active when admitted;
  if (durability class requires persistence?) then (durable)
    :Flush to DPU/OpenZFS; CXL pool is capacity tier,\nnot the durable storage ACK;
  endif
}
partition "Failure gate" {
  if (poison, link flap, fabric-manager loss, or p99 drift?) then (degrade)
    :Fence ownership_epoch, copy out if possible,\nmark pool AMBER/RED/DRAIN;
  else (healthy)
    :Expose pool pressure and locality to scheduler;
  endif
}
stop
'''),
"ADR-021_Heterogeneous_GP_GPU_Compute_and_Scheduler_Governance": diagram("ADR-021 - Heterogeneous GP-GPU Compute and Scheduler Governance", r'''
start
partition "Capability inventory" {
  :Discover accelerator vendor/model, HBM, interconnect,\ncollectives, precision, MIG/SR-IOV, driver/runtime;
  :Attach DPU/NIC/CXL/root-complex locality\nand qualified software stack profile;
}
partition "Profile match" {
  if (model runtime qualified for accelerator profile?) then (qualified)
    :Compute admission score by HBM, KV capacity,\ncollective topology, rail affinity, and SLO;
  else (not qualified)
    :Exclude from production placement; allow lab profile only;
  endif
  if (mixed-vendor collective path needed?) then (mixed)
    :Require explicit HCCL/NCCL/RCCL/oneCCL qualification\nwith latency and failure drill evidence;
  endif
}
partition "Placement" {
  if (same pod has model, KV, CXL pool, and healthy rails?) then (local)
    :Admit to local GPU/xPU set with Coherence lease;
  else (remote/cold)
    :Prewarm, migrate model, or reject if TTFT/TPOT budget fails;
  endif
}
partition "Governance" {
  :Publish only capability class and health state\nnot vendor-specific hidden topology to actors;
  :Continuously demote on driver drift, ECC/RAS errors,\nthermal throttling, rail errors, or DPU failure;
}
stop
'''),
"ADR-022_S3_Object_to_REST_API_Protocol_Mapping_Translator": diagram("ADR-022 - S3/Object REST Translator and Prefix-Cache Routes", r'''
start
partition "Ingress protocols" {
  :S3 client calls s3_net_service\nHTTP 8080 S3 object protocol;
  :REST client calls rest_net_service\nHTTP 8000 JSON/binary REST;
}
partition "Translation layer" {
  if (S3 request?) then (yes)
    :meta_translate_service normalizes\nmethod, bucket, key, query, headers;
    if (bucket maps to prefix-cache?) then (prefix)
      :Resolve namespace_mode, namespace,\noptional index_id, and prefix_id by policy;
    else (object)
      :Map to /objects/{bucket}/{key};
    endif
  else (REST native)
    :Validate route against OpenAPI contract;
  endif
}
partition "Prefix-cache contract" {
  if (exact put/get/delete?) then (exact)
    if (prefix_id present?) then (valid)
      :Route to /prefix-cache/{mode}/.../prefixes/{prefix_id};
    else (invalid)
      :Reject keyless exact operation\n400 invalid_identity;
      stop
    endif
  else (collection)
    :Search or invalidate requires explicit body\nand bounded predicate/escalation policy;
  endif
}
partition "Backend adapters" {
  :Use replaceable object, KV, vector,\nprefix-cache, and metadata adapters;
  :Emit metrics by operation, namespace_mode,\nindex_id, cache hit/miss, latency, error;
}
stop
'''),
"ADR-023_Coherence_CE_Namespace_Modalities": diagram("ADR-023 - Unified and Dimensional Indexed Namespaces", r'''
start
partition "Namespace selection" {
  :Receive Coherence-CE or translator request\nwith tenant, model, runtime, durability, trace;
  if (client simplicity or global logical identity dominates?) then (Unified)
    :Use Unified Namespace\nnamespace + prefix_id;
  else (locality-sensitive)
    :Use Dimensional Indexed Namespace\nnamespace + index_id + dimensions;
  endif
}
partition "Unified Namespace workflow" {
  if (Unified selected?) then (yes)
    :Exact path /prefix-cache/unified/{namespace}/prefixes/{prefix_id};
    :Search/invalidate at namespace collection route;
    :Coherence-CE hides region/datacenter/mesh routing;
  endif
}
partition "Dimensional index workflow" {
  if (Dimensional selected?) then (yes)
    :Validate index_id against tenant, region, datacenter,\nmesh_pool, pod/rack, model/runtime, class, epoch;
    :Exact path /prefix-cache/dimensional/{namespace}/indexes/{index_id}/prefixes/{prefix_id};
    if (miss and escalation authorized?) then (escalate)
      :Escalate to parent/region/global policy scope;
    else (bounded)
      :Stay index-local to bound latency and blast radius;
    endif
  endif
}
partition "Admission rollup" {
  :Roll metrics by namespace_mode, namespace, index_id,\nlocality_epoch, cache_kind, durability_class;
  if (telemetry stale or cross-DC p99 too high?) then (degrade)
    :Mark affected index or namespace AMBER/RED/DRAIN;
  else (healthy)
    :Admit local operations and preserve actor abstraction;
  endif
}
stop
'''),

}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for stem, content in sorted(DIAGRAMS.items()):
        (OUT / f"{stem}.puml").write_text(content, encoding="utf-8")
    print(f"wrote {len(DIAGRAMS)} PlantUML files to {OUT.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
