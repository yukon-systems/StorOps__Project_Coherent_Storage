# RAG Extraction and Source Map

Generated: 2026-05-17

- RAG PDFs scanned: 363
- Text extraction OK: 360
- Text extraction failed: 3

## Extraction failures

- `ibm-power9-lc921-lc922-family-3575pages.d942b834.pdf`: Syntax Error: Couldn't find trailer dictionary
Syntax Error: Catalog object is wrong type (null)
Syntax Error: Couldn't find trailer dictionary
Internal Error: xref num -1 not found but needed, try to reconstruct
Syntax Error: Couldn't find
- `id171-ccr2116-12g-4s-doc-220159.f98d8c32.pdf`: 
- `oe19-sled-outline-ref.26db1d40.pdf`: 

## Key sources

| ID | File | Text chars | Use |
| --- | --- | ---: | --- |
| S01 | `ualink-white-paper-publication-final-updated.6a11ffed.pdf` | 38372 | UALink open scale-up interconnect, rack-scale pod, bandwidth/latency/efficiency targets, SAI/Redfish ecosystem. |
| S02 | `unifabrix-ualink-webminar-20251210-pdf.2da3f553.pdf` | 48983 | UALink pod landscape, 800Gbps per port framing, CXL memory-pool adjacency, system-node terminology. |
| S03 | `understanding-intra-node-communication-hpc-systems.3b1067f4.pdf` | 96941 | Intra-node accelerator communication can interfere with inter-node traffic; pod designs need local/remote congestion modeling. |
| S04 | `open-cluster-designs-aligned-ai-inference-fabric-r.c994e6ef.pdf` | 131938 | OCP inference fabric RA: Minimal vs Distributed Inference, OPG/XOC sizes, gateway, telemetry, RoCE toggles, host/NIC tuning. |
| S05 | `ocp-open-cluster-designs-aligned-ai-training-fabri.a4f50f3e.pdf` | 156699 | OCP training fabric RA: OPG-M/XOC-N, rail-optimized/single-homed topologies, dual-plane 400G, RoCE QoS, lifecycle. |
| S06 | `ocp-mrc-1-0.d59de939.pdf` | 185922 | OCP Multipath Reliable Connection: packet spraying, SACK/NACK, congestion control and reliable multipath RDMA semantics. |
| S07 | `lossless-ethernet-design-guide-ai-fabrics-rocev2-2.ccf8088f.pdf` | 18903 | RoCEv2 lossless Ethernet guidance: PFC/ECN/DCQCN, MTU, telemetry, tuning risks. |
| S08 | `arista-ai-networking-building-lossless-ethernet-fa.f3be4e10.pdf` | 49278 | Lossless Ethernet for AI fabrics and packet-spraying/context for ECMP/RoCE operations. |
| S09 | `arista-broadcom-ai-networking-deployment-guide.c654bda1.pdf` | 57593 | Arista/Broadcom deployment guidance for AI Ethernet fabrics, QoS, ECN/PFC and operational tuning. |
| S10 | `amd-instinct-mi325x-pensando-pollara-gpu-cluster.c3b06df5.pdf` | 152676 | AMD Instinct + Pensando/Pollara cluster architecture evidence for GPU/NIC/DPU rail design. |
| S11 | `amd-pensado-400gbe-pollara-400-1q400p-product-brie.ce4c5a74.pdf` | 17920 | AMD Pensando Pollara 400GbE product brief: AI networking and RoCEv2 scale-out offload context. |
| S12 | `amd-pensando-pollara-400gbe-programmability-ai-net.3faf93f4.pdf` | 5901 | Pollara programmability and AI network telemetry/packet-spraying adjacency. |
| S13 | `intel-gaudi-3-ai-accelerator-cluster-ref-design-wh.9227fcb2.pdf` | 72543 | Intel Gaudi 3 cluster reference design: heterogeneous accelerator pod implications and RoCE/QoS tuning. |
| S14 | `hetccl-accelerating-llm-training-heterogeneous-gpu.1faeac80.pdf` | 133606 | HetCCL research: cross-vendor NVIDIA/AMD GPU collectives using RDMA without application changes. |
| S15 | `cxl-gpu-expanding-gpu-memory-capacity-arxiv-2506-1.ce395410.pdf` | 75211 | CXL-GPU research: GPU memory expansion using CXL and direct GPU storage expansion concepts. |
| S16 | `cxl-pnm-1m-token-llm-inference-kv-cache-arxiv-2511.794adce5.pdf` | 117052 | CXL-enabled processing-near-memory for long-context KV-cache management. |
| S17 | `tract-disaggregated-llm-serving-cxl-shared-memory.f94bd7ea.pdf` | 91416 | TraCT research: rack-scale CXL shared-memory KV cache for disaggregated LLM serving. |
| S18 | `cxl-4-0-statement-of-support-2025.f2bd38d2.pdf` | 7486 | CXL standards-roadmap evidence for future memory-pool evolution. |
| S19 | `cxl-3-1-statement-of-support-final-2024.4b83c90c.pdf` | 9831 | CXL 3.1 standards support evidence. |
| S20 | `nvidia-bluefield4-stx-storage-architecture-broad-a.3081f7ed.pdf` | 7189 | Adjacent AI-storage accelerator evidence for BlueField/STX; not direct UA-Link/CXL evidence. |
| S21 | `xsight-hammerspace-e1-800g-dpu-ai-warm-storage-202.812f4f3e.pdf` | 1286 | Adjacent DPU + AI warm storage evidence for DPU/network offload comparisons. |