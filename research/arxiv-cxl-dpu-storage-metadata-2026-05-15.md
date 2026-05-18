# arXiv CXL / DPU / Storage Metadata Sweep

Generated: 2026-05-15

API: arXiv export API Atom 1.0 (`https://export.arxiv.org/api/query`)

## API errors / limitations

- `cxl_general_latest`: `<HTTPError 429: 'Unknown Error'>` via `https://export.arxiv.org/api/query?search_query=all%3ACXL&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending`
- `compute_express_link_latest`: `<HTTPError 429: 'Too Many Requests'>` via `https://export.arxiv.org/api/query?search_query=all%3A%22Compute%20Express%20Link%22&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending`
- `cxl_kv_cache_latest`: `<HTTPError 429: 'Unknown Error'>` via `https://export.arxiv.org/api/query?search_query=all%3ACXL%20AND%20all%3A%22KV%20cache%22&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending`
- `dpu_rdma_storage_latest`: `<HTTPError 429: 'Unknown Error'>` via `https://export.arxiv.org/api/query?search_query=all%3ADPU%20AND%20all%3ARDMA&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending`
## Manual fallback latest candidates

The arXiv export API returned HTTP 429 during this run. The following high-signal candidates were retained or referenced through direct arXiv abs/PDF URLs and local RAG validation.

| arXiv ID | Title | Local/RAG status |
| --- | --- | --- |
| [2511.00321v1](https://arxiv.org/abs/2511.00321) | Scalable Processing-Near-Memory for 1M-Token LLM Inference: CXL-Enabled KV-Cache Management Beyond GPU Limits | `RAG-DATA/CXL-PNM-1M-Token-LLM-Inference-KV-Cache-arXiv-2511.00321v1.2025.pdf` |
| [2512.18194v1](https://arxiv.org/abs/2512.18194) | TraCT: Disaggregated LLM Serving with CXL Shared Memory KV Cache at Rack-Scale | `RAG-DATA/TraCT-Disaggregated-LLM-Serving-CXL-Shared-Memory-KV-Rack-Scale-arXiv-2512.18194v1.2025.pdf` |
| [2604.02442v1](https://arxiv.org/abs/2604.02442) | WIO: Upload-Enabled Computational Storage on CXL SSDs | `RAG-DATA/CXL-WIO-Upload-Enabled-Computational-Storage-on-CXL-SSDs-arXiv-2604.02442v1.2026.pdf` |
| [2506.15613v1](https://arxiv.org/abs/2506.15613) | From Block to Byte: Transforming PCIe SSDs with CXL Memory Protocol and Instruction Annotation | `RAG-DATA/CXL-From-Block-to-Byte-Bus-level-Addressable-CXL-SSDs-arXiv-2506.15613v1.2025.pdf` |

Manual fallback manifest: `RAG-DATA/ARCHIVE-ADD-V3-Arxiv-CXL-KV-Storage-Latest-2026-05-15.json`
