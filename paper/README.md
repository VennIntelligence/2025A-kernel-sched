# Paper Build Layout

This directory is organized around four paper outputs that share one asset pool:

- `src/en_conf` — English conference paper
- `src/zh_conf` — Chinese conference paper
- `src/en_supp` — English supplementary material
- `src/zh_supp` — Chinese supplementary material

Shared files live in:

- `common/` — LaTeX preamble, macros, metadata, and bibliography
- `assets/figures/` — all figures (every `\includegraphics` must go through `\ksFigure{}`)
- `assets/tables/` — shared table bodies `\input`-ted directly by section files

**All figure references must use the `\ksFigure{filename}` macro** defined in
`common/macros.tex`. Never write a raw relative path like `../../figures/...`;
`\ksFigure{}` resolves to `assets/figures/` and keeps all four outputs in sync.

## Compilation

Requires **XeLaTeX** and **latexmk**. Each output is built from its own
`src/<target>/main.tex`, but all share `common/` and `assets/`.

```bash
# Build one target
bash paper/build.sh en_conf
bash paper/build.sh zh_conf
bash paper/build.sh en_supp
bash paper/build.sh zh_supp

# Build all four
bash paper/build.sh all

# Remove build artefacts and dist PDFs
bash paper/build.sh clean
```

The build script runs `latexmk -xelatex` inside `src/<target>/`, writing
intermediate files to `paper/build/<target>/` and copying the final PDF to
`paper/dist/<target>.pdf`.

`zh_supp` depends on `zh_conf` for cross-references (`xr-hyper`); the script
builds `zh_conf` first automatically if needed.

## Directory map

```
paper/
  assets/
    figures/   ← single source of truth for all figures
    tables/    ← shared LaTeX table bodies
  common/
    preamble.tex      ← \usepackage, \graphicspath, layout defaults
    preamble_acm.tex  ← ACM-specific preamble variant
    macros.tex        ← \ksFigure{} and other shared commands
    metadata.tex      ← title, authors, affiliations
    references.bib
  src/
    en_conf/   zh_conf/   en_supp/   zh_supp/
      main.tex
      sections/
  build/       ← latexmk intermediate files (gitignored)
  dist/        ← final PDFs (gitignored)
```
