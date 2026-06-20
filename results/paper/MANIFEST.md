# Paper Experiment Manifest

All derived data for the paper and the notebooks is generated into this
directory by `scripts/paper/*.py`. The notebooks **only read** these files;
they never recompute metrics, so notebook output cannot drift from the
canonical numbers here.

**Naming convention**

- `e<N>_*` — **paper** experiments/figures (consumed by `paper/` via
  `sync_paper_artifacts.py` and rendered in `02_paper_figures`).
- `inv_*` — data **inventory / validation** tables (read by `01_data_and_problem`).
- `prob_*` — **problem-framing & benchmark-difficulty** tables, derived from the
  same source as the headline (`e1_headline.csv` `base_*` columns) plus
  `inv_case_summary.csv` (read by `01_data_and_problem`).
- `x<N>_*` — **explanatory, notebook-only** figure data. NOT paper figures;
  used by the notebooks to illustrate mechanisms the paper has no room for.

## CSV — paper experiments (`e*`)

- `e1_headline.csv` — E1 baseline vs promoted headline comparison for all 18 case/problem rows. **Single source of truth for the benchmark numbers** (`prob_*` derive from its `base_*` columns).
- `e2_victim_order.csv` — E2 P2 extra traffic and clean/dirty split across cases, orders, and eviction policies.
- `e2_victim_cv.csv` — E2 coefficient of variation of extra traffic across eviction policies for each case/order pair.
- `e5_residency_id_raw.csv` / `e5_residency_baseline.csv` — E5 Conv_Case0 L1 clean/dirty residency timeline (promoted / baseline order).
- `e6_surrogate.csv` / `e6_corr.csv` — E6 overflow-integral & peak-over-capacity surrogates vs P2 extra / P3 time, and their Spearman correlations.
- `e7_misalign.csv` — E7 P1 vs phi_best peak-residency metrics and worst capacity pressure.
- `e8_prefetch.csv` — E8 prefetch-window sweep over cases, two order families, and H values.
- `e9_working_set.csv` — E9 empirical minimum peak working set per case/cache across tested order families.
- `e10_portfolio.csv` — E10 autoresearch iteration win/loss/tie trajectory from ledger iterations 034-038.
- `e11_synth_ablation.csv` / `e11_synth_orders.csv` — E11 controlled clean-vs-dirty reserve ablation and order sweep on the synthetic kernel.
- `e12_baselines.csv` / `e12_winloss.csv` — E12 comparison against literature baselines (CP-list, pressure, Goodman–Hsu, …) and per-case win/loss.
- `e13_suite.csv` / `e13_summary.csv` — E13 synthetic suite results and aggregated summary.
- `e14_oracle.csv` — E14 ILP-oracle gap on small instances.
- `e16_runtime.csv` — E16 solver wall-clock runtime per instance/problem.

## CSV — data inventory (`inv_*`, from `inv_inventory.py`)

- `inv_file_inventory.csv` — raw JSON/CSV file census with sizes.
- `inv_case_summary.csv` — six-instance scale overview (nodes/edges/op-nodes/buffers/pipes). **Backs the paper's benchmark table.**
- `inv_json_csv_consistency.csv` — per-case JSON-vs-CSV parse agreement.
- `inv_field_completeness.csv` — required node-field completeness by case.
- `inv_op_distribution.csv` / `inv_pipe_distribution.csv` — operation-type and pipeline usage counts by case.
- `inv_cache_layer.csv` — allocated buffers by memory type (count/total/max size).
- `inv_edge_validation.csv` — self-loops, missing references, isolated nodes.
- `inv_buffer_consistency.csv` — buffer alloc/free balance and op-reference validity.
- `inv_dag_topology.csv` — DAG validity, components, root/leaf legality, generations.
- `inv_integrity_summary.csv` — pass/fail integrity roll-up per case.

## CSV — problem framing & difficulty (`prob_*`, from `prob_metrics.py`)

- `prob_overview.csv` — structured P1/P2/P3 objective/output/metric comparison.
- `prob_capacities.csv` — on-chip cache capacities (from `ks_core.constants`). **Backs the supplement's capacity table.**
- `prob_baseline_metrics.csv` — 18-row baseline metric table (from `e1_headline.csv` `base_*`).
- `prob_p1.csv` — P1 peak residency + capacity ratios.
- `prob_p2.csv` — P2 spills, extra, and spill density (per op-node).
- `prob_time.csv` — P1/P2/P3 baseline time pivot with ratios.
- `prob_difficulty.csv` — normalised cross-case difficulty indicators (column max = 1).

## CSV — explanatory figures (`x*`, notebook-only)

- `x1_dag_nodes.csv` / `x1_dag_edges.csv` / `x1_dag_occupancy.csv` — Conv_Case0 DAG (nodes with op/mem/gen/sched_pos, edges) and per-step L1/UB occupancy for the schedule-walk figure (`x1_dag_walk.py`).
- `x2_clean_dirty_timeline.csv` / `x2_cost_split.csv` — Conv_Case0 L1 clean/dirty residency timeline and the clean-vs-dirty spill-cost decomposition (`x2_clean_dirty.py`).
- `x3_portfolio_traj.csv` — cumulative-best portfolio trajectory over iterations 034-038 with per-problem win breakdown and aggregate pressure; win/loss totals validated against `e10_portfolio.csv` (`x3_portfolio_traj.py`).

## Figures — paper (`e*`)

Rendered by `02_paper_figures` into `output/02_paper_figures/*.png` (and `e15_applicability.png` by `e15_applicability.py`), then copied to `paper/assets/figures/` by `sync_paper_artifacts.py`:
`e2_victim_sensitivity`, `e3_order_sensitivity`, `e4_clean_dirty_composition`, `e5_peak_residency`, `e6_surrogate`, `e7_misalignment_worst_ratio`, `e8_decoupling`, `e9_working_set`, `e10_portfolio`, `e11_synth_generality`, `e12_baselines`, `e13_synth_suite`, `e14_oracle`, `e15_applicability`.

## Figures — explanatory, notebook-only (`x*`)

Rendered by `03_results_report` / `01_data_and_problem`; **not** copied into the paper:
`x1_dag_walk` (real-case DAG + schedule occupancy), `x2_clean_dirty_steps` (clean/dirty cost mechanism), `x3_portfolio_trajectory` (search trajectory).

## Synthetic instances

- `data/processed/synthetic/Synthetic_Case0_clean.json` / `Synthetic_Case0_dirty.json` — E11 synthetic capacity-bound kernel (clean reserve via COPY_IN vs dirty reserve via compute); regenerate via `scripts/paper/e11_synth_generality.py`.

## Other

- `PAPER_NUMBERS.yml` — declarative macro manifest consumed by `sync_paper_artifacts.py` to emit `paper/assets/tables/numbers.tex`.
- `complexity_analysis.md` — prose complexity write-up.

## Notebooks

- `notebooks/01_data_and_problem/` — data inventory, validation, and P1/P2/P3 problem framing (reads `inv_*` / `prob_*`, plus the `x1` walk-through).
- `notebooks/02_paper_figures/` — the canonical factory for every paper figure (`e*`).
- `notebooks/03_results_report/` — English narrative tying figures and numbers to claims C1/C2/C3 + criterion D + method M (embeds `e*` figures, adds `x2`/`x3`).
