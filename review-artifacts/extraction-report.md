# RAG Extraction Report

Generated: 2026-05-13

- Text cache: `/tmp/project-coherent-rag-text`
- Supplemental text cache: `/tmp/project-coherent-rag-text-extra`
- PDFs already extracted before this refresh: 204
- PDFs extracted during the base refresh: 12
- PDFs extracted during the Intel BMRA/QAT supplement: 2
- PDF extraction failures after this refresh: 1

## Newly extracted PDFs

| File | Text bytes |
| --- | ---: |
| `DCF-Power-Distribution-LVDC-white-paper-version-1.0_FINAL.pdf` | 442191 |
| `HVDC_LVDC_PSU_18kW-Spec_1.0.0.pdf` | 102834 |
| `OBMF-ICP-over-USB-1.0.pdf` | 33785 |
| `OCP-MRC-1.0.pdf` | 185922 |
| `OCP-OCS_White_Paper_April_2026_FINAL.pdf` | 62583 |
| `OCP-Open-Cluster-Designs-Aligned-AI-Training-Fabric-RA.pdf` | 156699 |
| `OCP-Open-Data-Center-for-AI-Whitepaper-FINAL.pdf` | 20321 |
| `ORV3-HVDC-LVDC-100kW-Power-Shelf-Spec_1.0.0.pdf` | 61751 |
| `Open-Cluster-Designs-Aligned-AI-Inference-Fabric-Reference-Architecture.pdf` | 131938 |
| `Server_MHS_DC-SCM-Specs-and-Designs---OpenCompute.pdf` | 28118 |
| `Test-Guide-for-Data-Center-Timing.pdf` | 54603 |
| `Whitepaper_OCP_Ready-Requirements-Energy-Storage-Systems-Final.pdf` | 124489 |

## Extraction failures

| File | Return code | Error |
| --- | ---: | --- |
| `IBM_POWER9_LC921_LC922_Family-3575pages.pdf` | 1 | Syntax Error: Couldn't find trailer dictionary / Syntax Error: Catalog object is wrong type (null) / Syntax Error: Couldn't find trailer dictionary / Internal Error: xref num -1 not found but needed, try to reconstruct / Syntax Error: Couldn't find trailer dictionary / Syntax Error: Couldn't find tr |

## Non-PDF extraction policy

- Native text-like files are classified directly from their content.
- Images, CAD, board, spreadsheet, archive, and mechanical files are retained as binary/reference evidence and classified from path/name only unless a later manual review needs them.

## Intel BMRA/QAT supplemental PDFs

These PDFs were added to the on-host RAG corpus after the base 250-file refresh and extracted into `/tmp/project-coherent-rag-text-extra`.

| File | Text bytes | Source ID | ADR impact |
| --- | ---: | --- | --- |
| `Intel-Network-Edge-Container-Metal-Reference-Systems-Architecture-User-Guide.1706608508.pdf` | 163684 | R251 | BMRA automation, BIOS/kernel/IOMMU/SR-IOV/hugepages/device-plugin, telemetry, QAT context, and post-deployment verification gates. |
| `Intel-QAT-Latest-8960-C3000.pdf` | 344623 | R252 | QAT crypto/compression acceleration, Xen/SR-IOV/VF/PF, trusted-assignment assumptions, endpoint/reset hazards, and virtualization caveats. |
