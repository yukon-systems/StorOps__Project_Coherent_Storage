# IETF/IRTF Chunking and Manifest Source Map

**Generated:** 2026-05-20

This source map records protocol references for adapting CCNx chunking and ICN manifest concepts into Coherence-CE object chunking, S3 multipart mapping, Git LFS gateway behavior, and RAG corpus storage boundaries.

## Source status summary

| Source | Current status used here | Architecture use |
| --- | --- | --- |
| `draft-irtf-icnrg-ccnxchunking-04` | Internet-Draft, intended Experimental, published 2026-02-07, expires 2026-08-11. Work in progress; not a standards-track RFC. | Reference pattern for ordered chunk numbering, final-chunk metadata, and fixed chunk-size disclosure. |
| `draft-irtf-icnrg-flic-07` | Internet-Draft, intended Experimental, published 2025-03-03, expired 2025-09-04. | Reference pattern for manifest graphs, content hashes, collection metadata, and traversal. |
| RFC 8569 | IRTF Experimental RFC for CCNx semantics. | Reference for CCNx Content Object and Interest semantics. |
| RFC 8609 | IRTF Experimental RFC for CCNx TLV message format. | Reference for CCNx TLV encoding and message extension context. |
| Git LFS API docs | Active upstream Git LFS API documentation. | Normative compatibility target for any Git LFS facade exposed above Coherence-CE. |
| Git LFS Batch API docs | Active upstream Git LFS Batch API documentation. | Defines `/objects/batch` behavior for upload/download negotiation. |
| Git LFS File Locking API docs | Active upstream Git LFS locking documentation. | Defines lock creation/list/delete/verify behavior and lock-verification push safety. |

## Architecture interpretation

Project Coherent Storage should not expose CCNx chunking or FLIC directly as public client protocols. Instead, Coherence-CE should use their design ideas internally:

1. external protocols remain S3, Git LFS, REST, and Coherence-native APIs;
2. Coherence-CE represents large byte objects as immutable content-addressed chunks;
3. an object manifest names ordered chunks, chunk sizes, chunk hashes, final chunk number, durability class, and placement policy;
4. readers observe only committed manifests;
5. abandoned partial uploads are garbage-collected by manifest lease and namespace policy;
6. semantic RAG chunks remain separate from byte-storage chunks.

## Source URLs

- CCNx chunking datatracker page: https://datatracker.ietf.org/doc/draft-irtf-icnrg-ccnxchunking/
- CCNx chunking text: https://www.ietf.org/archive/id/draft-irtf-icnrg-ccnxchunking-04.txt
- FLIC datatracker page: https://datatracker.ietf.org/doc/draft-irtf-icnrg-flic/
- FLIC text: https://www.ietf.org/archive/id/draft-irtf-icnrg-flic-07.txt
- RFC 8569: https://www.rfc-editor.org/rfc/rfc8569
- RFC 8609: https://www.rfc-editor.org/rfc/rfc8609
- Git LFS API: https://github.com/git-lfs/git-lfs/blob/main/docs/api/README.md
- Git LFS Batch API: https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md
- Git LFS File Locking API: https://github.com/git-lfs/git-lfs/blob/main/docs/api/locking.md
