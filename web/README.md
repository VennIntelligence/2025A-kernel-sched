# Project website

Bilingual React/TypeScript project page for **Dependency-Frontier Scheduling
with Asymmetric-Cost Spill Planning for NPU Kernels**.

## Public narrative

The site separates three evidence layers:

- **Production portfolio:** four legal structural orders, true best-fit,
  two victim policies, bounded reload windows, and canonical P2/P3 selection.
- **Offline cost repair:** nonuniform Conv0/Conv1 case studies, reported as
  exploratory mechanism evidence rather than one six-case algorithm.
- **Fixed-order oracle:** weighted residency-gap selection followed by
  contiguous packing and canonical validation. A valid artifact that reaches
  the lower bound is a fixed-order traffic certificate, not global order
  optimality or full P2 lexicographic optimality.

Public production results are five P2 wins and one tie, and five P3 time wins
with one Conv1 loss. The three machine-checkable traffic certificates are
Conv0/frontier 57,408, Conv0/P1 81,504, and FA0/id_raw 3,584.

The supported mechanism account is `Tr = Vol + Dt`: every strict public P2 win
reduces total spill volume, while the generated surcharge changes differently
across cases. Geometric peak or overflow-area proxies do not reliably rank
orders; Conv0/frontier has larger logical overflow area but 29.6% lower
certified fixed-order traffic than the legacy P1 order.

Synthetic evidence is bounded. The canonical 36-case re-evaluation supports
portfolio non-regression, while eight 17-node oracle cases support small-scale
same-order agreement. Neither establishes new generalization over the
predecessor.

The interactive contest explainer under `src/components/problem/` and
`src/assets/problem.md` is a deliberately preserved teaching section. Research
narrative updates must not rewrite its five-stage walkthrough.

## Development

```bash
npm install
npm run dev
npm run lint
npm run build
```

Vite writes the production build to `web/dist/`.

## Content map

| Path | Responsibility |
| --- | --- |
| `src/lib/i18n.ts` | Complete Chinese and English copy; keep both languages aligned |
| `src/data/paperTables.ts` | Production P2/P3 numbers and bounded research-evidence rows |
| `src/sections/` | Page-level narrative components |
| `src/components/problem/` | Frozen interactive explanation of the contest artifact model |
| `src/App.css` | Shared academic-page styling |
| `public/figures/` | Current PNG figures derived from the paper figure pipeline |

## Editing rules

- Trace every public number to a machine-readable artifact.
- Do not mix official P2 and P3 schedules or objectives.
- Keep production outcomes separate from repair and fixed-order oracle evidence.
- Describe COPY_IN membership as a static **backed** label, not a dynamic
  clean/dirty state; the evaluator lacks explicit read/write roles.
- State outcome boundaries: P2 is 5 wins + 1 tie, P3 time is 5 wins + 1 loss,
  repair is nonuniform, and exact certificates cover fixed-order traffic only.
- Treat the canonical synthetic suite as non-regression evidence, not a new
  generalization result.
- Use current paper PNGs instead of rebuilding analytical charts in React.
- Preserve the affiliation as “Venn Intelligence Foundation.”
