# ADR-020: CXL Memory Pools for UA-Link Pods

**Project:** Project Coherent Storage  
**Version:** 2026-Q2.v4  
**Status:** Proposed  
**Generated:** 2026-05-17

## Decision summary

Use CXL memory pools as governed pod-local T1/T1.5 capacity behind Coherence-CE. CXL pools may relieve warm KV, prefix, metadata, vector-index, and model/object pressure, but do not change actor-visible APIs and do not create durability unless device semantics prove persistence and recovery.

## Decision

- Treat CXL pools as memory resources owned by Coherence-CE and scheduler policy, not by vLLM adapters.
- Prefer same-pod and same-root-complex CXL placement for warm KV/prefix staging.
- Require pool ownership epoch, fabric-manager health, link state, RAS/error counters, thermal state, p99 latency, bandwidth, failover behavior, and rollback target.
- Keep KV-D0 active decode in GPU HBM/local DRAM unless local benchmarks explicitly qualify CXL for a narrow decode-adjacent role.
- Use CXL-KV, CXL-GPU, CXL-PNM, and rack-scale CXL shared-memory research as experiment tracks only until production evidence exists.
- Keep OpenZFS durability beneath Coherence-CE; CXL block/persistent roles require the ADR-015 media qualification gate.

## Acceptance criteria

- CXL pool inventory is attached to pod topology and scheduler locality.
- Pool admission distinguishes volatile memory, persistent memory, block-presented media, and rejected devices.
- Pool loss, stale ownership, fabric-manager failure, link downshift, thermal throttling, and memory-poison events have failure semantics.
- Coherence-CE can demote from CXL to DRAM/T2/OpenZFS-backed classes under pressure.

## Source documents

- V4-S15/V4-S16/V4-S17: CXL-GPU and CXL/KV research.
- V4-S18/V4-S19: CXL standards support.
- v3 Marvell/XConn/CXL evidence retained in inherited ADR-015 and ADR-016.
