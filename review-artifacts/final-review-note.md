# Final Review Note: Project Coherent Storage ADR Package

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Package:** Inference persistence and API ADR set, RAG refresh 2026-05-13  
**Status:** Proposed  
**Generated:** 2026-05-13

## Review scope

This package starts from the reviewed inference-optimized ADR package and adds the missing implementation decisions requested for Coherence-CE policy, vLLM adapter contracts, failure semantics, scheduler admission, and CXL/PMem hardware-tier governance.

The changes preserve the user-confirmed layering:

```text
vLLM / peer inference actors
  -> Coherence-CE Memory Mesh APIs only
    -> Coherence-CE owns KV identity, placement, hydration, replication, persistence, metrics, and admission summaries
      -> OpenZFS/NVMe-oF durable NAND block substrate
        -> DPU/SmartNIC-handled storage-network offload and RDMA resource mediation
          -> RoCEv2 fabric and platform/facility services
```

Inference actors use Coherence-CE APIs only and are not configured with OpenZFS, DPU, NVMe-oF, RoCEv2, or RDMA details. They receive Coherence-CE API results: hit/miss, payload reference, durability class/state, recompute/degrade/queue/reject reason, and scheduler-safe admission hints.

## Added ADRs

| ADR | Added decision |
| --- | --- |
| ADR-010 | Coherence-CE write policy to OpenZFS is selected by KV durability class: write-around for active decode, write-back/write-behind for recomputable reusable prefix state, and write-through for durable/session/governed classes. |
| ADR-011 | KV-D0 through KV-D5 define ack, persistence, TTL, eviction, loss/recompute, fencing, and scheduler behavior. |
| ADR-012 | vLLM adapters receive an exact Coherence-native API plus OpenAI-compatible metadata/header contract; lower-layer implementation controls are forbidden. |
| ADR-013 | Failure semantics cover runtime, Coherence, storage, DPU, fabric, rack power/thermal, timing, telemetry, and scheduler failure domains by KV class. |
| ADR-014 | Coherence-CE metrics roll up into scheduler GREEN/AMBER/RED/DRAIN admission summaries by tenant, model, class, prefix shard, and locality scope. |
| ADR-015 | CXL is governed as a placement-sensitive T1/T1.5 memory tier; OpenZFS-adjacent CXL use is role-qualified; Optane PMem 200/300-class constraints are compared against CXL openness, packaging flexibility, and topology risk. |

## Added API and operations artifacts

| Artifact | Purpose |
| --- | --- |
| `api/coherence-ce-vllm-adapter.openapi.yaml` | OpenAPI 3.1 contract for Coherence-native vLLM adapter operations: lookup, publish, reserve, flush, promote, evict, health, and admission summary. |
| `api/openai-compatible-extension-contract.md` | Defines how `/v1/chat/completions` and `/v1/responses` clients may provide Coherence hints while preserving standard response shapes. |
| `operations/failure-semantics-matrix.md` | Operator-facing failure matrix mapping failure modes to KV-D0 through KV-D5 behavior and scheduler state. |
| `operations/scheduler-admission-rollup.md` | Operator-facing rollup model for Coherence metrics into admission decisions and decision logs. |

## Source grounding

The ADRs continue to use the RAG manifest, the local `processing-cache/project-coherent-rag-text` extraction cache, and the same-day Intel BMRA/QAT supplemental extraction cache at `processing-cache/project-coherent-rag-text-extra`. The key local source anchors are:

- R01 for vLLM/PagedAttention KV-cache memory pressure, block identity, sharing, and preemption.
- R02/R03/R30 for scheduler, TTFT/TPOT, and inference-serving SLOs.
- R04/R21/R22/R23 for ML I/O behavior and OpenZFS operational considerations.
- R05/R06/R07/R08/R09/R15 for DPU/RDMA/offload and storage-path concerns.
- R10 through R20 plus R34/R37/R39 for RoCEv2, multipath, fabric isolation, and observability.
- R31 through R42 for power, timing, management, and platform/facility admission signals.
- R251/R252 for Intel BMRA deployment automation, BIOS/kernel/IOMMU/SR-IOV/hugepage/device-plugin preparation, QAT deployment context, and QAT crypto/compression trust, reset, VF/PF, Xen, endpoint, and fallback limits.
- R28/R29 plus Optane RAG references for CXL/PMem memory-tier direction, CXL pooling/telemetry, and Optane PMem/SSD comparison points.

The package also cites official documentation not present in the on-host RAG set:

- O01 Oracle Coherence read-through/write-through/write-behind caching documentation.
- O02 Oracle Coherence cache persistence documentation.
- O03 Oracle Coherence metrics documentation.
- O04 OpenZFS `sync` property documentation.
- O05 OpenZFS VDEV/log-device documentation.
- O06 OpenZFS scrub/resilver documentation.
- O07 OpenZFS ZIO scheduler documentation.
- O08 OpenAI Chat Completions OpenAPI specification.
- O09 OpenAI Responses OpenAPI specification.
- O10 CXL Consortium About CXL official description.
- O11 CXL Consortium CXL memory form-factor comparison.
- O12 Intel Optane PMem 200 product and compatibility documentation.
- O13 Intel Optane PMem 300 announcement and 4th Gen Xeon overview.
- O14-O18 Marvell Structera CXL product, product-brief, switch, and XConn acquisition references.
- O19-O24 XConn Apollo/Apollo 2, dynamic allocation, ScaleFlux interoperability, and MemVerge memory-sharing references.
- O25-O29 OCP CMS/CFM logical architecture, fabric management, hotness tracking, memory-fabric orchestration, and 2025 OCP CXL/CMS references.

## Explicit architectural positions

- Cross-node OpenZFS/NVMe-oF mirrored NAND is still a core gated substrate requirement, not experimental-only.
- The coherent NAND substrate is below Coherence-CE and not in the active per-token vLLM contract.
- DPU/SmartNIC hardware is still a strict storage-path requirement for NVMe-oF hardware offload and RDMA memory/resource mediation.
- Intel QAT is a separate host/platform crypto/compression accelerator, not a DPU substitute and not an RDMA/NVMe-oF storage-path authority.
- Host-mediated fallback is degraded resilience, not the normal storage-path architecture.
- QAT-enabled paths require trusted assignment, current PF/VF ownership, driver/firmware evidence, endpoint/reset telemetry, and qualified CPU fallback or drain behavior.
- Coherence-CE decides write-around/write-back/write-through behavior from durability class and policy.
- Durable acknowledgements for KV-D3 through KV-D5 require backing-store evidence; KV-D2 pending write-back is not misrepresented as durable.
- The OpenAI-compatible surface remains a compatibility surface, not a storage-control API.
- Scheduler admission consumes Coherence-CE summaries and reason codes rather than vLLM or client-provided storage/fabric details.
- CXL intent is explicit but governed: use CXL for warm Coherence/OpenZFS-adjacent memory expansion only when role, persistence, root-complex/NUMA placement, switch/bifurcation state, fabric-manager/CFM state, pool ownership, latency, telemetry, and rollback are qualified.
- CXL is preferred over Optane PMem as the forward-looking heterogeneous memory-expansion path because it is an open PCIe/CXL ecosystem usable beyond Intel-only PMem platforms and supports AIC, U.3-class, and EDSFF packaging; that flexibility creates mandatory physical-placement governance.
- CXL must not be hidden behind opaque PCIe switching, oversubscribed fabrics, or auto-bifurcated switch paths for latency-sensitive Coherence, OpenZFS, DPU, or GPU roles.
- Explicit CXL switch fabrics are allowed as managed T1.5 warm/shared memory pools only after local qualification; Marvell/XConn/OCP references make this a current governed option, not an automatic hot-path default.
- Volatile CXL never provides durable acknowledgement; persistent or block-presented CXL must prove flush, power-loss, endurance, mirroring, replacement, and import behavior before any durable OpenZFS role.

## Validation targets

The package should pass these local checks before review handoff:

- README indexes ADR-001 through ADR-015.
- All new ADRs have package metadata and source documents sections.
- OpenAPI YAML parses.
- Coherence-native schema contains KV-D0 through KV-D5, lookup, publish, reserve, flush, promote, evict, health, and admission summary endpoints.
- vLLM-facing OpenAPI schemas do not expose lower-layer implementation identifiers.
- Operations docs include failure and admission behavior by KV durability class and CXL topology/latency/fabric-manager/pool-ownership fault class.
- QAT validation proves trusted PF/VF assignment, host-driver/removal quiesce gates, q35/VM compatibility where used, crypto/compression correctness, decompression buffer guards, endpoint reset behavior, and CPU fallback/drain scheduler reason-code rollup.
- CXL validation proves role classification, OCP CMS topology class, source-of-truth topology, same-root-complex preference, hidden switch/bifurcation rejection, explicit CXL switch-fabric qualification, CXL-vs-DRAM latency measurement, OpenZFS role limits, and scheduler reason-code rollup.
- Historical package snapshots remain available for comparison.
