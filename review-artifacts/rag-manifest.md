# RAG Manifest Summary

Generated: 2026-05-13; supplemented: 2026-05-13 with Intel BMRA/QAT PDFs

- RAG root: `RAG-DATA`
- Total files: 252
- PDF files: 219
- Extracted PDFs: 218
- Failed/missing PDF extractions: 1
- Native text files: 1
- Image-only files: 17
- Binary/reference files: 11
- Other non-PDF references: 4

## Impact count by ADR

| ADR | Primary | Supporting | Background |
| --- | ---: | ---: | ---: |
| ADR-001 | 108 | 72 | 37 |
| ADR-002 | 5 | 15 | 45 |
| ADR-003 | 2 | 9 | 28 |
| ADR-004 | 65 | 77 | 55 |
| ADR-005 | 21 | 30 | 41 |
| ADR-006 | 9 | 38 | 59 |
| ADR-007 | 31 | 65 | 72 |
| ADR-008 | 2 | 33 | 129 |
| ADR-009 | 7 | 51 | 63 |
| ADR-013 | 1 | 1 | 0 |
| ADR-014 | 1 | 1 | 0 |
| ADR-015 | 2 | 5 | 0 |

## Post-refresh supplemental sources

| ID | Source file | Extraction | ADR impact |
| --- | --- | --- | --- |
| R251 | `Intel-Network-Edge-Container-Metal-Reference-Systems-Architecture-User-Guide.1706608508.pdf` | Extracted to `processing-cache/project-coherent-rag-text-extra` (163684 text bytes). | BMRA deployment automation, BIOS/kernel/IOMMU/SR-IOV/hugepages/device-plugin, telemetry, and post-deployment verification gates. |
| R252 | `Intel-QAT-Latest-8960-C3000.pdf` | Extracted to `processing-cache/project-coherent-rag-text-extra` (344623 text bytes). | QAT crypto/compression acceleration, supported 8960/C3000-era platforms, Xen/SR-IOV/VF/PF limits, trust assumptions, reset/driver hazards, and virtualization caveats. |

See `rag-manifest.json` for the complete file-level manifest.
