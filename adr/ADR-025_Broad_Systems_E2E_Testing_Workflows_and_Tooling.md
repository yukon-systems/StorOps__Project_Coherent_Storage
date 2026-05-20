# ADR-025: Broad-Systems E2E Testing Workflows and Tooling

**Project:** Project Coherent Storage
**Architecture cycle:** 2026-Q2
**Status:** Proposed
**Generated:** 2026-05-19

## Architecture diagram

![ADR-025_Broad_Systems_E2E_Testing_Workflows_and_Tooling](diagrams/ADR-025_Broad_Systems_E2E_Testing_Workflows_and_Tooling.png)

Printable sections:

- [Section 01 - plan, allocation, fast gates](diagrams/ADR-025_Broad_Systems_E2E_Testing_Workflows_and_Tooling_print-section-01_plan-fast-gates.png)
- [Section 02 - architecture path, load, failure](diagrams/ADR-025_Broad_Systems_E2E_Testing_Workflows_and_Tooling_print-section-02_architecture-load-failure.png)
- [Section 03 - platform semantics, collect, gate](diagrams/ADR-025_Broad_Systems_E2E_Testing_Workflows_and_Tooling_print-section-03_platform-collect-gate.png)

## Decision summary

Define the workflow and tooling architecture for broad-systems testing and end-to-end testing (E2ET) across Project Coherent Storage. E2ET must validate full architecture behavior from the user/API layer through load balancers, Coherence-CE, LLM serving/cache, scheduler admission, RDMA/RoCEv2 fabric, DPU/NVMe-oF, OpenZFS storage, CXL memory tiers, and observability.

The E2ET harness must be:

- **HPC-oriented** with SLURM as the primary scale-out execution substrate;
- **scheduler-modular** with adapters for local, Flux, OpenPBS/PBS Pro, Nomad, Kubernetes, or other site schedulers;
- **cross-platform** across Linux, FreeBSD, Solaris, and illumos variants;
- **LLVM/Clang-first** with GCC allowed only by documented exception;
- **failure-semantics aware** so tests prove fencing, drain, degraded mode, recovery, and telemetry freshness;
- **artifact-complete** so every run retains raw logs, normalized JSON, scheduler metadata, and telemetry snapshots.

## Context

Component benchmarks are necessary but insufficient. Project Coherent Storage is a layered architecture where correctness and performance depend on interactions between multiple services and hardware planes. A system can pass fio, iperf3, and pgbench independently while failing the actual inference path due to cache invalidation, scheduler mis-admission, DPU telemetry staleness, RDMA rail degradation, or OpenZFS resilver interference.

E2ET therefore needs a workflow model that composes tests across layers, injects failures, drives realistic traffic, captures telemetry, and produces decision-grade acceptance results.

## Decision

Adopt a staged E2ET workflow with a common manifest, scheduler adapter, evidence bundle, and gate engine.

```yaml
e2e_test:
  test_id: pcs.e2e.inference-storage.failure-rail-a.v1
  intent: failure-mode
  topology: pod-scale-lab
  scheduler:
    adapter: slurm
    allocation:
      exclusive: true
      components:
        - role: loadgen
          nodes: 2
        - role: api_lb
          nodes: 2
        - role: coherence_mesh
          nodes: 3
        - role: model_server
          gres: gpu:4
        - role: storage
          nodes: 3
  platform_matrix:
    linux: required
    freebsd: supported-for-network-storage-proxy-roles
    solaris_illumos: supported-for-zfs-nfs-proxy-observability-roles
  phases:
    - provision
    - smoke
    - warmup
    - baseline
    - inject_failure
    - sustained_load
    - recovery
    - collect_artifacts
    - gate
  gates:
    max_error_rate: 0.001
    max_ttft_p99_ms: 750
    max_tpot_p99_ms: 80
    recovery_deadline_s: 120
    telemetry_freshness_s: 15
```

## E2ET workflow phases

| Phase | Purpose | Example tools | Gate |
| --- | --- | --- | --- |
| Provision | Create or select known-good hosts, services, networks, storage pools, and scheduler allocations. | Ansible, shell, CMake/CTest fixtures, Terraform/OpenTofu where applicable, SLURM `sbatch`. | Required resources allocated and versions captured. |
| Unit | Validate harness libraries, parsers, fixtures, and control-plane code. | CTest, pytest, Bats, GoogleTest/Catch2, Google Benchmark for microbench code. | All unit tests pass before lab resources are used. |
| Smoke | Verify service starts and minimal path works. | curl, k6 smoke, pytest requests, service-native health checks. | One request/operation succeeds per service role. |
| Functional | Validate required API/storage/cache behavior. | pytest, CTest, Bats, OpenAPI client tests, S3 client tests. | Correctness invariants pass with representative data. |
| Warmup | Stabilize caches, JITs, model load, ARC/L2ARC, CXL placement, and connection pools. | service-native warmers, vLLM/SGLang warm prompts, fio preconditioning. | No acceptance metrics collected until warmup completes. |
| Baseline | Capture steady healthy behavior before injecting failure or peak load. | k6/Locust/wrk, fio, iperf3, pgbench, MLPerf/Triton/vLLM/SGLang. | Establish in-run green baseline. |
| Failure injection | Trigger controlled failure or degradation. | switch port disable, service kill, DPU reset, zpool degrade, firewall rule change, latency/loss tool. | Expected alarms, drain, fencing, and admission state changes occur. |
| Sustained load | Run representative multi-service workload long enough to expose queues, thermal drift, compaction, scrub, or leaks. | SLURM job arrays, heterogeneous jobs, k6/Locust distributed mode, fio/IOR, model-server benchmarks. | Error and p99/p999 gates remain within profile. |
| Peak performance | Sweep load until a declared SLO gate fails. | job arrays, parameter sweeps, k6 stages, vLLM/SGLang concurrency sweeps. | Capacity envelope is recorded, not hidden. |
| Recovery | Remove failure and verify service returns to safe admission state. | service restart, network restore, zpool attach/clear, scheduler re-admission. | Recovery deadline and data correctness pass. |
| Artifact collection | Collect raw logs, metrics, configs, tool output, profiles, core dumps if any, and result JSON. | Prometheus snapshot, OTLP export, journal/log collection, `scontrol show job`, platform counters. | Evidence bundle complete. |
| Gate | Reduce raw evidence into decision result. | Python gate evaluator, jq, CTest/pytest reports, markdown summary. | `PASS`, `WARN`, `FAIL`, or `INCONCLUSIVE`. |

## Tooling baseline by test class

| Test class | Baseline tool options | Notes |
| --- | --- | --- |
| Unit tests | CTest for compiled projects, pytest for Python harness logic, Bats for shell, GoogleTest/Catch2 where already used. | Unit tests do not require SLURM unless they validate scheduler adapters. |
| Smoke tests | curl/httpie, k6 single-VU scripts, pytest requests, service-native health checks. | Must run before long allocations consume cluster time. |
| Functional tests | pytest, CTest, Bats, OpenAPI-generated clients, S3 clients, Coherence-CE contract tests. | Validate correctness before performance. |
| Failure-mode tests | Harness-controlled service kill, link disable, DPU reset, zpool degrade, firewall rule changes, latency/loss injection. | Must include rollback and operator-safe blast radius. |
| Sustained-load tests | k6, Locust distributed mode, fio, IOR/MDTest, pgbench, iperf3, MLPerf/Triton/vLLM/SGLang. | Requires telemetry and thermal/power/context capture. |
| Peak tests | SLURM job arrays, k6 stages, Locust shape classes, vLLM/SGLang concurrency sweeps, fio queue-depth sweeps. | Peak tests map capacity; failing at high load is valid if envelope is recorded. |
| Soak tests | Same as sustained load with longer duration and stricter artifact collection. | Include leak detection, storage growth, retry rates, and telemetry freshness. |
| Regression tests | Compare current normalized JSON to previous green baseline. | Use fixed workloads, fixed tool versions, and explicit tolerance windows. |

## Broad architecture E2E profiles

### Profile A: API to inference cache to storage substrate

1. Generate OpenAI-compatible chat/completion traffic through the global/regional/datacenter load-balancer chain.
2. Route to Coherence-CE, then to vLLM/SGLang/Triton/Ollama/LocalAI/LM Studio/LM Link-compatible model servers.
3. Exercise prefix-cache hits, misses, invalidation, and durability class transitions.
4. Force warm-tier hydration through CXL/DRAM and durable object fetch through DPU/OpenZFS.
5. Gate on TTFT, TPOT, cache hit rate, error rate, scheduler admission state, and storage p99.

### Profile B: Storage under inference load

1. Run inference traffic at a declared sustained rate.
2. Run fio/IOR/MDTest against NFS/object/OpenZFS paths.
3. Start OpenZFS scrub/resilver or mirror degradation drill.
4. Verify scheduler reduces or preserves admission according to ADR-013 and ADR-014.
5. Gate on inference SLOs, dirty bytes, ZFS latency, DPU queue health, and recovery deadline.

### Profile C: Network and DPU failure semantics

1. Establish baseline RDMA/RoCEv2 and NVMe-oF behavior.
2. Degrade one rail, inject packet loss, or reset a DPU namespace path.
3. Verify fencing, drain, reroute, and telemetry alerts.
4. Continue representative traffic.
5. Gate on no stale data, bounded errors, and recovery within deadline.

### Profile D: Cross-platform service-role validation

1. Run Linux model-server and RDMA roles where accelerator stack requires Linux.
2. Run FreeBSD or Solaris/illumos NFS, proxy, firewall, ZFS, or observability roles where available.
3. Validate that service-level contracts remain portable even when platform-specific acceleration is absent.
4. Mark unsupported accelerator-native tests as `INCONCLUSIVE` or `SKIPPED_PLATFORM`, not failed architecture behavior.

## SLURM execution model

SLURM profiles must use one of these modes:

| Mode | Use case | Required metadata |
| --- | --- | --- |
| Single batch job | Smoke, unit, small functional tests. | job ID, node, partition, exit code. |
| Job array | Parameter sweeps such as fio queue depth, k6 VUs, vLLM concurrency, or CXL memory placement. | array ID, task ID, parameter manifest, result shard. |
| Heterogeneous job | Multi-role E2E tests with loadgen, API, model, storage, and telemetry roles. | role-to-node map, component allocation, per-role logs. |
| Dependent jobs | Stage-based workflows: provision -> warmup -> load -> failure -> collect. | dependency graph and stage result. |
| Exclusive allocation | Decision-grade performance benchmarks. | proof of exclusive node/GPU allocation and noisy-neighbor controls. |

Non-SLURM scheduler adapters must expose equivalent semantics in the normalized result manifest: allocation ID, role placement, resource shape, start/end times, exit codes, and artifact locations.

## Cross-platform implementation call-outs

Tests must separate **feature validation** from **backend qualification**.

Example for heterogeneous compute:

| Feature | Portable validation | Backend-specific qualification |
| --- | --- | --- |
| OpenAI-compatible model server path | k6/Locust/vLLM/SGLang HTTP profile against `/v1/chat/completions` or `/v1/completions`. | CUDA/TensorRT, ROCm, oneAPI/SYCL, Metal, or vendor NPU-specific benchmark profile. |
| Model artifact execution | ONNX Runtime CPU or available execution provider, service-level correctness test. | TensorRT engine, ROCm EP, oneDNN/OpenVINO EP, CUDA EP, vendor runtime. |
| Prefix-cache semantics | Coherence-CE contract test: hit/miss/invalidate/stale behavior. | vLLM/SGLang backend cache implementation and GPU memory behavior. |
| Distributed collective or hetero compute | MPI/SYCL/oneAPI/HetCCL-style abstraction test where available. | NCCL, RCCL, oneCCL, vendor fabric plugin. |

Linux-only CUDA failures must not invalidate FreeBSD or Solaris/illumos service roles. Instead, the result must identify the feature as portable and the backend as not supported on that platform.

## Failure semantics requirements

E2ET must cover these failure domains over time:

- API/load-balancer process crash and reload;
- DNS/service-discovery stale target;
- Coherence-CE mesh node loss;
- model-server GPU out-of-memory or backend unavailable;
- prefix-cache stale epoch or invalidation race;
- RDMA rail degradation, PFC/ECN drift, or packet loss;
- DPU telemetry stale, namespace reset, or queue-pair failure;
- OpenZFS disk loss, mirror degradation, scrub/resilver interference;
- CXL tier demotion or page-placement failure;
- NFS/object service partial outage;
- telemetry pipeline outage.

Failure tests must declare blast radius and rollback before execution. Production-impacting or destructive tests require an explicit maintenance window and operator approval.

## Evidence bundle contract

Every E2ET run must produce:

```json
{
  "test_id": "pcs.e2e.inference-storage.failure-rail-a.v1",
  "result": "PASS",
  "started_at": "2026-05-19T10:00:00-07:00",
  "ended_at": "2026-05-19T12:00:00-07:00",
  "scheduler": {
    "adapter": "slurm",
    "job_id": "123456",
    "nodes": ["node-a", "node-b"],
    "exclusive": true
  },
  "platforms": ["linux", "freebsd"],
  "toolchain": {
    "cc": "clang",
    "cxx": "clang++",
    "gcc_exception": false
  },
  "metrics": {
    "ttft_p99_ms": 620,
    "tpot_p99_ms": 73,
    "error_rate": 0.0002,
    "recovery_s": 84
  },
  "artifacts": {
    "raw_logs": "artifacts/raw/",
    "normalized_json": "artifacts/result.json",
    "prometheus_snapshot": "artifacts/prometheus.json",
    "slurm_metadata": "artifacts/slurm.json"
  }
}
```

## CI/CD integration

CI/CD must run tests in increasing cost order:

1. static validation and manifest schema checks;
2. unit tests;
3. smoke tests using local or ephemeral services;
4. functional tests against a small lab topology;
5. scheduled SLURM benchmark sweeps;
6. scheduled E2ET failure-mode and sustained-load campaigns;
7. pre-release capacity-envelope and soak tests.

Long-running SLURM tests must be explicit pipeline stages with run IDs and artifact retention. They must not silently run as part of a lightweight pull-request check.

## Consequences

### Positive

- Full-system correctness and performance can be evaluated as architecture behavior, not isolated tool output.
- SLURM job arrays and heterogeneous jobs provide a scalable way to sweep profiles and coordinate multi-role tests.
- Cross-platform limitations become explicit call-outs rather than hidden false failures.
- Failure semantics become testable acceptance criteria.

### Negative

- E2ET requires more lab orchestration and artifact storage than component tests.
- Some failure injections need privileged access and maintenance windows.
- Scheduler adapters must preserve enough semantics to keep results comparable across SLURM and non-SLURM environments.

### Deferred

- Machine-readable JSON Schema for E2ET manifests and result bundles.
- Automated dashboard generation from evidence bundles.
- Formal E2ET profile registry with signed baselines.
- Multi-site E2ET federation across regions.

## Acceptance criteria

- E2ET profiles can run under SLURM with job ID and role placement captured.
- Equivalent local/non-SLURM adapter output uses the same normalized result structure.
- Tests are classified as unit, smoke, functional, failure-mode, sustained-load, peak, soak, or regression.
- Linux-only accelerator paths are documented as backend-specific qualification, not portable feature requirements.
- All decision-grade E2ET runs include raw logs, normalized JSON, telemetry snapshot, scheduler metadata, and explicit gate result.

## References

- Slurm `sbatch`: https://slurm.schedmd.com/sbatch.html
- Slurm `srun`: https://slurm.schedmd.com/srun.html
- Slurm heterogeneous jobs: https://slurm.schedmd.com/heterogeneous_jobs.html
- Slurm job arrays: https://slurm.schedmd.com/job_array.html
- CTest documentation: https://cmake.org/cmake/help/latest/manual/ctest.1.html
- pytest documentation: https://docs.pytest.org/en/stable/contents.html
- Bats Core: https://github.com/bats-core
- k6 documentation: https://grafana.com/docs/k6/latest/testing-guides/load-testing-websites/
- Locust documentation: https://docs.locust.io/en/stable/index.html
- fio documentation: https://fio.readthedocs.io/
- iperf3 documentation: https://software.es.net/iperf/
- MLCommons inference benchmark repository: https://github.com/mlcommons/inference
- MLPerf inference submission guide: https://docs.mlcommons.org/inference/submission/
- NVIDIA Triton Performance Analyzer: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/perf_analyzer/README.html
- vLLM serving benchmark: https://docs.vllm.ai/en/stable/api/vllm/benchmarks/serve.html
- SGLang benchmarking: https://docs.sglang.io/developer_guide/benchmark_and_profiling.html
- ONNX Runtime performance documentation: https://onnxruntime.ai/docs/performance/
- SYCL oneAPI specification: https://oneapi-spec.uxlfoundation.org/specifications/oneapi/v1.3-rev-1/elements/sycl/source/
