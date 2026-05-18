# ADR-017: Research Metadata and arXiv Publication Workflow

**Project:** Project Coherent Storage  
**Architecture cycle:** 2026-Q2  
**Status:** Proposed  
**Generated:** 2026-05-15

## Architecture diagram

![ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow](diagrams/ADR-017_Research_Metadata_and_Arxiv_Publication_Workflow.png)

## Decision summary

Maintain the research package as Markdown plus arXiv-oriented LaTeX and BibTeX. Research refreshes should use arXiv metadata APIs and arXiv bulk-data options when available, but must record rate limits, query failures, and manual fallback steps as part of the evidence trail.

## Context

The package is intended to be publishable as a technical research artifact. arXiv submission guidance requires careful TeX preparation, portable source packaging, and reliable references. During this run, calls to the arXiv export API returned HTTP 429 rate-limit responses. That limitation is captured in `research/arxiv-cxl-dpu-storage-metadata-2026-05-15.json` rather than hidden.

## Decision

- Keep source documents in Markdown for project review and in LaTeX/BibTeX for arXiv-style publication.
- Prefer arXiv export API metadata for latest research sweeps when rate limits allow.
- Use arXiv bulk-data guidance for larger-scale refresh pipelines instead of scraping individual pages at scale.
- Record API query strings, timestamps, HTTP failures, and retry requirements in the package.
- Keep BibTeX entries stable and cite local RAG filenames in comments where useful.
- Do not claim that the package is arXiv-submission complete until it compiles under a TeX engine and references are checked.

## Required artifacts

| Artifact | Purpose |
| --- | --- |
| `reports/*.md` | Human-reviewable report source. |
| `latex/project-coherent-storage.tex` | arXiv-oriented manuscript source. |
| `latex/references.bib` | Reference database. |
| `latex/README-arxiv-submission.md` | Submission checklist and local validation boundary. |
| `research/arxiv-cxl-dpu-storage-metadata-*.json` | Metadata query results, API failures, and latest-paper candidates. |
| `diagrams/*.puml` | Diagram source. |
| `diagrams/*.png` / `*.svg` | Rendered figures for reports and LaTeX. |

## Acceptance criteria

- Markdown report exists and has no placeholder sections.
- LaTeX and BibTeX files exist and reference rendered diagrams.
- BibTeX citation keys used in LaTeX exist in `references.bib`.
- arXiv API/bulk-data guidance is cited in the report or submission README.
- Any local compilation gap is explicit.
