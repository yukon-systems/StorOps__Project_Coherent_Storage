# ADR-024: System-Level Benchmarking Suite Definitions

**Project:** Project Coherent Storage
**Architecture cycle:** 2026-Q2
**Status:** Proposed
**Generated:** 2026-05-19

## Architecture diagram

![ADR-024_System_Level_Benchmarking_Suite_Definitions](diagrams/ADR-024_System_Level_Benchmarking_Suite_Definitions.png)

Printable sections:

- [Section 01 - manifest, scope, scheduler](diagrams/ADR-024_System_Level_Benchmarking_Suite_Definitions_print-section-01_manifest-scope-scheduler.png)
- [Section 02 - platform call-outs and evidence gates](diagrams/ADR-024_System_Level_Benchmarking_Suite_Definitions_print-section-02_platform-evidence-gates.png)

## Decision summary

Define a governed system-level benchmarking suite taxonomy for Project Coherent Storage. Benchmark suites must be organized by:

1. **Component type**: CPU, memory, disk, filesystem, network, accelerator, DPU/SmartNIC, CXL, and platform telemetry.
2. **Service type**: NFS, object/S3, OLTP, HTTP/REST API, load balancer, firewall, LLM model server, LLM cache, HTTP proxy/cache, vector store, scheduler, observability services, and other primary-ordinal service-layer systems that have domain-specific benchmark tools.
3. **Test intent**: unit, smoke, functional, failure-mode, regression, sustained-load, peak-performance, spike, soak, capacity-envelope, and acceptance-gate tests.
4. **Execution mode**: local developer run, CI run, lab-node run, SLURM job-array run, SLURM heterogeneous job run, and alternate scheduler run.

The benchmarking program must be HPC-oriented, scheduler-aware, reproducible, and cross-platform across Linux, FreeBSD, Solaris, and illumos variants. Linux-only or vendor-specific accelerators are permitted only behind explicit call-outs and abstraction layers.

## Context

The existing ADR set defines inference SLOs, cache locality, RDMA, DPU, OpenZFS, CXL, UA-Link, heterogeneous compute, scheduler admission, and failure semantics. Those decisions need a benchmark taxonomy that prevents ad-hoc single-tool results from being mistaken for architecture validation.

Project Coherent Storage must benchmark both the physical substrate and the services layered on top of it. A CPU microbenchmark does not validate an LLM cache. An LLM serving benchmark does not validate OpenZFS mirror behavior. An NFS throughput result does not validate metadata storm behavior, failure recovery, or scheduler admission. Benchmark evidence must therefore be collected as a suite with declared scope, platform, workload profile, toolchain, telemetry, and acceptance gate.

## Decision

Adopt the following benchmark suite contract for every system benchmark:

```yaml
benchmark_suite:
  suite_id: pcs.component.cpu.llvm-build.v1
  owner: storage-architecture
  intent: sustained-load
  component_type: cpu
  service_type: none
  scheduler:
    primary: slurm
    compatible_adapters: [local, flux, openpbs, nomad, kubernetes]
  platforms:
    linux: required
    freebsd: required-when-tooling-exists
    solaris_illumos: required-when-tooling-exists
  toolchain:
    compiler_default: clang
    gcc_allowed: false
    notes: GCC may be used only when an upstream benchmark cannot build with LLVM/Clang.
  workload:
    duration: 30m
    warmup: 5m
    repetitions: 5
    isolation: dedicated-node-or-exclusive-allocation
  telemetry:
    required: [wall_time, cpu_utilization, memory_bandwidth, power_if_available, thermals_if_available]
    export: [json, prometheus_snapshot, slurm_job_metadata]
  gate:
    compare_to: previous_green_baseline
    max_regression_percent: 5
    required_confidence: medium
```

A benchmark result is not architecture evidence unless it includes:

- benchmark suite ID and version;
- exact host, firmware, kernel, driver, compiler, and tool versions;
- scheduler allocation metadata, including SLURM job ID when applicable;
- warmup duration, run duration, repetition count, and random seeds where applicable;
- raw tool output plus normalized JSON summary;
- platform call-outs for Linux-only, FreeBSD-only, Solaris/illumos-only, CUDA-only, ROCm-only, oneAPI/SYCL-only, or vendor-specific paths;
- acceptance result: `PASS`, `WARN`, `FAIL`, or `INCONCLUSIVE`.

## Benchmark taxonomy

### Component benchmark suites

| Component type | Primary questions | Baseline tool options | Required metrics |
| --- | --- | --- | --- |
| CPU | Scalar, vector, compiler, crypto, compression, and build throughput. | SPEC CPU where licensed, Phoronix Test Suite/OpenBenchmarking CPU suites, Google Benchmark for C++ microbenchmarks, timed LLVM/Clang builds, OpenSSL speed. | elapsed time, throughput, cycles if available, thermals, power if available, compiler flags. |
| Memory | Bandwidth, latency, NUMA placement, CXL tier behavior, allocator sensitivity. | STREAM, lmbench-like latency probes, Phoronix memory suite, custom C/LLVM pointer-chase and memcpy kernels. | GB/s, ns latency, NUMA node, CXL tier, page size, allocator, p50/p95/p99. |
| Disk/block | Random/sequential IO, sync writes, queue depth, latency distribution, write amplification. | fio, diskinfo where available, vendor NVMe tools, OpenZFS `zpool iostat`. | IOPS, bandwidth, p50/p95/p99/p999 latency, CPU cost, fsync latency, media errors. |
| Filesystem/metadata | Metadata storm, create/stat/unlink, snapshot/scrub/resilver impact. | fio file workloads, IOR, MDTest, Phoronix disk/filesystem profiles, ZFS tooling. | ops/s, p99 metadata latency, ARC/L2ARC hit rate, dirty data, scrub/resilver state. |
| Network | TCP, UDP, RDMA/RoCEv2, packet loss, jitter, ECN/PFC behavior. | iperf3 with JSON, OSU Micro-Benchmarks for MPI, RDMA perftest where supported, switch telemetry. | throughput, p99 latency, retransmits, drops, ECN marks, PFC pause, CPU cost. |
| Accelerator | GPU/NPU/APU/TPU compute, memory copy, kernel latency, framework backend behavior. | MLPerf Inference where applicable, Triton Performance Analyzer, ONNX Runtime perf tools, oneAPI/SYCL samples, vendor tools. | TTFT, TPOT, tokens/s, batch latency, HBM utilization, copy time, power, errors. |
| DPU/SmartNIC | NVMe-oF/RDMA offload, crypto/compression, isolation, telemetry freshness. | vendor qualification tools, fio over NVMe-oF, iperf3/RDMA tests, custom queue-depth probes. | offload utilization, QP/MR errors, p99 IO latency, telemetry age, failover time. |
| CXL | Memory tier latency, bandwidth, placement correctness, degradation behavior. | STREAM-like tier tests, pointer-chase latency, allocator placement probes, Coherence-owned synthetic KV warm-tier tests. | GB/s, ns latency, page placement, eviction rate, failure/demotion time. |

### Service benchmark suites

| Service type | Baseline tool options | Primary gates |
| --- | --- | --- |
| NFS server | fio over NFS, IOR, MDTest, client-side `nfsstat`/system counters. | read/write p99, metadata ops/s, mount option disclosure, server CPU, network saturation. |
| OLTP server | PostgreSQL `pgbench`, sysbench OLTP for MySQL-compatible systems, HammerDB when cross-database comparability is needed. | TPS, p95/p99 transaction latency, failed transactions, client saturation check. |
| HTTP/REST API server | k6, Locust, wrk/wrk2, hey, ApacheBench for simple smoke only. | request throughput, p95/p99/p999 latency, error rate, saturation point. |
| Load balancer | k6/wrk against HAProxy, Caddy, Nginx, or equivalent with backend echo services and LB metrics enabled. | accepted connections/s, backend selection correctness, TLS cost, reload/drain behavior. |
| Firewall | iperf3/packet generators across PF/UFW/nftables/ipfilter rulesets plus platform counters. | throughput by rule profile, connection setup rate, dropped packet correctness, fail-closed behavior. |
| LLM model server | MLPerf Inference, NVIDIA Triton Performance Analyzer, vLLM benchmark serving, SGLang bench serving, Ollama/LocalAI/LM Studio/LM Link/OpenAI-compatible k6/Locust profiles. | TTFT, TPOT, inter-token latency, tokens/s, goodput, error rate, GPU memory. |
| LLM cache | vLLM/SGLang prefix-cache benchmarks, Coherence-CE cache probes, synthetic prompt reuse traces. | cache hit rate, prefill avoided, TTFT reduction, invalidation correctness, stale-hit rate. |
| HTTP proxy/cache | Squid/Varnish/nginx-cache tests using k6/wrk/Locust through proxy path plus cache metrics. | hit/miss ratio, origin offload, revalidation correctness, p99 proxy latency. |
| Object/S3 layer | MinIO warp or equivalent S3 workload tool, fio/object gateway adapters, custom multipart tests. | PUT/GET latency, list latency, multipart throughput, checksum errors, retry rate. |
| Vector/retrieval service | dataset-specific recall/latency profiles, ANN benchmarks, service-native benchmark clients. | recall@k, p99 search latency, index build time, memory footprint, stale-index behavior. |

## Test intent definitions

| Test intent | Definition | Example |
| --- | --- | --- |
| Unit test | Validates one function, parser, manifest rule, or small library boundary. | Validate benchmark manifest schema with Python tests. |
| Smoke test | Confirms a service starts and one trivial request succeeds. | Start HAProxy and issue one health-check request. |
| Functional test | Confirms a required behavior across realistic inputs. | Verify S3 multipart upload produces the expected checksum. |
| Regression test | Compares current behavior with a previous green baseline. | Fail if p99 REST latency regresses by more than 5%. |
| Failure-mode test | Injects one failure and validates fencing/recovery semantics. | Disable one RDMA rail and verify admission demotes affected profiles. |
| Sustained-load test | Runs representative load long enough to expose thermal, memory, queue, or compaction effects. | Run NFS + OLTP + inference load for 6 hours. |
| Peak-performance test | Finds maximum throughput under declared constraints. | Sweep vLLM concurrency until TTFT/TPOT gate fails. |
| Spike test | Applies abrupt load changes to test autoscaling and queue behavior. | Jump from 10% to 150% expected API rate for 5 minutes. |
| Soak test | Runs steady load for extended reliability validation. | 24-hour Coherence-CE cache + OpenZFS scrub coexistence run. |
| Capacity-envelope test | Maps safe operating ranges by sweeping resource dimensions. | Sweep fio queue depth, request size, and mirror degradation state. |

## Scheduler and HPC execution rules

SLURM is the primary benchmark scheduler. Benchmark harnesses must support:

- `sbatch` batch execution;
- `srun` per-step launch;
- job arrays for parameter sweeps;
- heterogeneous jobs for multi-role tests such as client, load balancer, API server, storage target, and telemetry collector;
- exclusive node allocation when a benchmark result is intended as performance evidence;
- capture of SLURM job ID, node list, partition, constraints, cgroups, CPU/GPU binding, and environment.

Harnesses must remain scheduler-modular. A benchmark suite may be executed through local shell, Flux, OpenPBS/PBS Pro, Nomad, Kubernetes, or other schedulers if the result manifest records the scheduler adapter and resource allocation semantics.

## Cross-platform implementation call-outs

Every benchmark suite must include a platform call-out table when behavior differs by OS, compiler, driver, or accelerator backend.

| Capability | Linux | FreeBSD | Solaris/illumos | Call-out rule |
| --- | --- | --- | --- | --- |
| Default compiler | LLVM/Clang required. | LLVM/Clang required where available. | LLVM/Clang preferred; vendor compiler only when required. | GCC must not be a hard dependency unless an upstream benchmark requires it and the exception is documented. |
| CUDA | Supported only on qualified NVIDIA/Linux stacks. | Not a baseline requirement. | Not a baseline requirement. | Use abstraction or skip with `INCONCLUSIVE`, not `FAIL`, when CUDA is not a platform feature. |
| ROCm | Linux-oriented qualification path. | Not a baseline requirement. | Not a baseline requirement. | Prefer ONNX Runtime, SYCL, oneAPI, or service-level OpenAI-compatible tests when ROCm is unavailable. |
| oneAPI/SYCL | Candidate heterogeneous abstraction path. | Candidate if toolchain exists. | Candidate if toolchain exists. | Must record compiler/runtime implementation and target device. |
| DTrace | Optional on Linux where available. | Available platform capability. | Native platform capability. | Prefer DTrace call-outs on FreeBSD/Solaris/illumos for kernel/service probes. |
| eBPF/perf | Linux-specific. | Not portable baseline. | Not portable baseline. | Linux-only observability may supplement but not replace portable metrics. |

For heterogeneous GP-GPU compute, benchmark suites should prefer service-level and portable abstraction tests first: ONNX Runtime execution providers, SYCL/oneAPI kernels, OpenAI-compatible HTTP model-server tests, MLPerf LoadGen where applicable, and Coherence-CE cache probes. Vendor-native CUDA, ROCm, TensorRT, or platform-specific paths are valid only as qualified backend profiles.

## Baseline options

Minimum baseline suites for a new lab cluster:

1. `pcs.component.cpu.clang-build`: timed LLVM/Clang build workload with fixed source tarball and flags.
2. `pcs.component.memory.stream`: memory bandwidth and latency tier probe.
3. `pcs.component.disk.fio`: fio random read/write, sequential read/write, and sync-write profiles.
4. `pcs.component.network.iperf3`: iperf3 TCP/UDP JSON runs per rail and traffic class.
5. `pcs.service.nfs.ior-mdtest`: NFS throughput and metadata profile.
6. `pcs.service.oltp.pgbench`: PostgreSQL pgbench with separate client host.
7. `pcs.service.http.k6`: HTTP/REST API load test with smoke, sustained, spike, and peak profiles.
8. `pcs.service.lb.haproxy`: load-balancer profile with backend drain and reload tests.
9. `pcs.service.llm.vllm-sglang`: TTFT/TPOT/goodput profile for OpenAI-compatible model servers.
10. `pcs.service.cache.coherence-prefix`: prefix-cache hit/miss/invalidation benchmark.

## Consequences

### Positive

- Benchmark results become comparable across commits, clusters, and operating systems.
- SLURM-based sweeps can scale from one node to full pod-level test campaigns.
- Component tests and service tests are separated, preventing misleading evidence.
- Platform-specific accelerator limitations are explicit instead of hidden as failures.

### Negative

- Requires more harness metadata than ad-hoc benchmarking.
- Some benchmark tools are Linux-first or vendor-first and need platform call-outs.
- Licensed suites such as SPEC require separate access and cannot be assumed in all CI lanes.

### Deferred

- Formal machine-readable schema for benchmark suite manifests.
- Automated trend dashboards and admission-control gates from benchmark history.
- Signed benchmark result bundles for cross-site evidence exchange.

## Acceptance criteria

- Benchmark manifests declare component type, service type, test intent, scheduler adapter, platform support, toolchain, telemetry, and acceptance gate.
- New benchmark suites default to LLVM/Clang where compilation is required.
- SLURM execution is first-class, but non-SLURM adapters can run the same manifest shape.
- Linux-only, CUDA-only, ROCm-only, or vendor-specific paths are documented as call-outs.
- Raw output and normalized JSON are retained for every benchmark run used as architecture evidence.

## References

- Slurm `sbatch`: https://slurm.schedmd.com/sbatch.html
- Slurm `srun`: https://slurm.schedmd.com/srun.html
- Slurm heterogeneous jobs: https://slurm.schedmd.com/heterogeneous_jobs.html
- Slurm job arrays: https://slurm.schedmd.com/job_array.html
- fio documentation: https://fio.readthedocs.io/
- iperf3 documentation: https://software.es.net/iperf/
- OpenBenchmarking.org suites: https://openbenchmarking.org/suites/
- SPEC CPU benchmarks: https://www.spec.org/cpu/
- CTest documentation: https://cmake.org/cmake/help/latest/manual/ctest.1.html
- pytest documentation: https://docs.pytest.org/en/stable/contents.html
- Bats Core: https://github.com/bats-core/bats-core
- Google Benchmark: https://github.com/google/benchmark
- k6 documentation: https://grafana.com/docs/k6/latest/
- Locust documentation: https://docs.locust.io/en/stable/
- PostgreSQL pgbench: https://www.postgresql.org/docs/current/pgbench.html
- Redis benchmark guidance: https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/benchmarks/
- NVIDIA Triton Performance Analyzer: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/perf_analyzer/README.html
- vLLM serving benchmark: https://docs.vllm.ai/en/stable/api/vllm/benchmarks/serve.html
- SGLang benchmarking: https://docs.sglang.io/developer_guide/benchmark_and_profiling.html
- MLCommons inference benchmark repository: https://github.com/mlcommons/inference
