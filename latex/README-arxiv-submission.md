# arXiv submission notes for Project Coherent Storage

This directory contains an arXiv-oriented source draft, not a completed submission.

## Files

- `project-coherent-storage.tex` - LaTeX manuscript source.
- `references.bib` - BibTeX reference file.
- `figures/*.png` - rendered PlantUML diagrams referenced by the manuscript.

## arXiv guidance consulted

- TeX submission guidance: https://info.arxiv.org/help/submit_tex.html
- References FAQ: https://info.arxiv.org/help/faq/references.html
- Article preparation guidance: https://info.arxiv.org/help/prep.html
- Bulk data access: https://info.arxiv.org/help/bulk_data/index.html

## Local validation boundary

This host currently has `bibtex` and `plantuml`, but no `pdflatex`, `latexmk`, or `tectonic`. Therefore the manuscript source was syntax/structure checked locally, but not compiled into a PDF on this host.

Before submission, run on a TeX-capable host:

```sh
pdflatex project-coherent-storage.tex
bibtex project-coherent-storage
pdflatex project-coherent-storage.tex
pdflatex project-coherent-storage.tex
```

Then inspect the produced PDF, bibliography, figure placement, and overfull/underfull warnings.

## Source-package checklist

- Keep `.tex`, `.bib`, and referenced figures in the uploaded source bundle.
- Do not include local absolute paths.
- Confirm every `\cite{...}` key exists in `references.bib`.
- Confirm all figures referenced by `\includegraphics` exist.
- If the paper is converted from this project package, avoid exposing private local paths or non-public notes.
- Use evidence-grade language for all vendor/partnership claims.


## Current manuscript note

The manuscript source is `project-coherent-storage.tex`; it reuses `references.bib` and neutral figure filenames.
