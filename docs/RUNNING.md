# Running the kernel-scheduling pipeline

End-to-end, copy-pasteable commands for every stage, verified against the
current (post-reorg) layout. Unless noted, **run every command from the repo
root** (`kernal_scheduling/`).

The repo is a `uv` workspace. `ks-core` (the `src/ks_core` package) is installed
editable into `.venv`, so scripts that `import ks_core` work without any
`PYTHONPATH` juggling as long as you run them through `uv run` (or the project
`.venv` interpreter).

## Repo map (entry points)

| Area | Path | Purpose |
| --- | --- | --- |
| Core library | `src/ks_core/` | `solver`, `plotting`, `data_utils`, `graph`, `io`, `metrics`, `evaluator`, `constants` |
| Promoted algorithm | `algorithms/ours/solve.py` | re-exports `ks_core.solver.solve` (final iter038 candidate) |
| Baseline algorithm | `algorithms/baseline/solve.py` | reference baseline |
| AutoResearch process state | `autoresearch/` | iterations, `ledger.csv`, `best_iter.txt` (process, not method) |
| Experiment runner | `experiments/run_experiment.py` | YAML-config-driven; loads `algorithms.<name>.solve` |
| Experiment configs | `experiments/configs/*.yaml` | e.g. `exp001_baseline01.yaml` |
| Paper experiment scripts | `scripts/paper/*.py` | regenerate `results/paper/*.csv` (SSOT) |
| Artifact sync | `scripts/paper/sync_paper_artifacts.py` | CSVs -> `paper/assets/{tables,figures}` |
| Paper SSOT data | `results/paper/*.csv`, `PAPER_NUMBERS.yml` | regeneratable, **not** git-tracked |
| Notebooks (read-only) | `notebooks/0{1,2,3}_*/*.ipynb` | render figures/report from `results/paper/` |
| Paper build | `paper/build.sh`, `paper/.latexmkrc`, `paper/src/<target>/` | 4 targets -> `paper/dist/<target>.pdf` |

## 0. Environment setup

```bash
make setup            # installs uv if missing, then: uv sync --all-extras
# or directly:
uv sync --all-extras
```

This creates `.venv/` with Python 3.12 and installs `ks-core` editable plus all
deps (numpy, pandas, networkx, matplotlib, seaborn, jupyter, ortools, ...).

Sanity check the import surface:

```bash
uv run python -c "import ks_core; from ks_core import solver, plotting, data_utils; print('ok')"
```

Run the unit tests:

```bash
make test             # uv run pytest -v
```

## 1. Run experiments (solver / baseline)

The runner loads the algorithm named in the config from `algorithms/<name>/solve.py`.

```bash
# Canonical baseline reference (writes results/exp001_baseline01/)
uv run python experiments/run_experiment.py experiments/configs/exp001_baseline01.yaml
# equivalently:
make run CONFIG=experiments/configs/exp001_baseline01.yaml
```

Validate / compare produced schedules:

```bash
make validate         # uv run python scripts/validate_schedule.py --dir results/
make compare          # uv run python scripts/compare_results.py
```

Quick solver-correctness gate (golden spill numbers for 3 cases):

```bash
uv run python scripts/paper/_t0_verify.py
```

## 2. Regenerate the paper data (results/paper SSOT CSVs)

Each `scripts/paper/*.py` is standalone and takes no arguments; it writes its
own CSV(s) into `results/paper/`. Run the full set:

```bash
for s in scripts/paper/e1_headline.py scripts/paper/e2_victim_order.py \
         scripts/paper/e5_residency.py scripts/paper/e6_corr.py \
         scripts/paper/e6_surrogate.py scripts/paper/e7_misalign.py \
         scripts/paper/e8_prefetch_sweep.py scripts/paper/e9_working_set.py \
         scripts/paper/e10_portfolio.py scripts/paper/e11_synth_generality.py \
         scripts/paper/e12_baselines.py scripts/paper/e13_synth_suite.py \
         scripts/paper/e14_ilp_oracle.py scripts/paper/e15_applicability.py \
         scripts/paper/e16_runtime.py scripts/paper/inv_inventory.py \
         scripts/paper/prob_metrics.py scripts/paper/x1_dag_walk.py \
         scripts/paper/x2_clean_dirty.py scripts/paper/x3_portfolio_traj.py \
         scripts/paper/baselines.py; do
  echo "=== $s ==="; uv run python "$s" || { echo "FAILED: $s"; break; }
done
```

Notes:
- `e13_synth_suite.py` is the slowest (synthetic suite); the whole sweep takes a
  couple of minutes total.
- `e16_runtime.csv` records wall-clock timings, so it is the only CSV expected
  to differ between runs. Every other CSV regenerates byte-identically.
- `e10_portfolio.py` / `x3_portfolio_traj.py` read `autoresearch/ledger.csv` and
  depend on `results/exp001_baseline01/metrics.json` (stage 1) being present.

## 3. Generate paper figures & tables (sync artifacts)

After the CSVs exist, sync the LaTeX number/table includes and copy figures into
`paper/assets/`:

```bash
uv run python scripts/paper/sync_paper_artifacts.py
```

Writes `paper/assets/tables/{numbers,headline_results,headline_summary,remaining_losses}.tex`
and refreshes `paper/assets/figures/`.

## 4. Execute the notebooks (read-only renders)

The three notebooks **only read** from `results/paper/` (regenerate it first,
stage 2). They locate the repo root automatically, so they run both from Jupyter
Lab and headless.

Headless (executes top-to-bottom, embeds outputs in place):

```bash
for nb in notebooks/01_data_and_problem/01_data_and_problem.ipynb \
          notebooks/02_paper_figures/02_paper_figures.ipynb \
          notebooks/03_results_report/03_results_report.ipynb; do
  uv run jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=900 "$nb"
done
```

Notebook figure outputs land under `output/<notebook-name>/` (gitignored).
Run order matters: `03_results_report` embeds PNGs produced by
`02_paper_figures`, so execute 02 before 03.

Interactive:

```bash
make notebook         # uv run jupyter lab --notebook-dir=notebooks
```

> The Makefile `build-nb` / `build-all-nb` targets and
> `scripts/build_notebook.py` / `scripts/build_all_notebooks.py` are the **old
> fragment-based** builder (they expect `fragments/` subdirs that no longer
> exist). The current notebooks are standalone `.ipynb` files; use the
> `nbconvert` commands above instead.

## 5. Build the paper PDFs

Requires a TeX distribution with `latexmk` + `xelatex` on `PATH`
(e.g. MacTeX / TeX Live).

```bash
bash paper/build.sh all        # all four targets
# or one at a time:
bash paper/build.sh en_conf
bash paper/build.sh zh_conf
bash paper/build.sh en_supp    # auto-builds en_conf first (xr cross-refs)
bash paper/build.sh zh_supp    # auto-builds zh_conf first
bash paper/build.sh clean      # rm -rf paper/build paper/dist
```

Outputs:

```
paper/dist/en_conf.pdf
paper/dist/zh_conf.pdf
paper/dist/en_supp.pdf
paper/dist/zh_supp.pdf
```

The supplement targets depend on their conference counterpart's `.aux`
(`xr` cross-references), which `build.sh` handles automatically. Regenerate the
artifact includes (stage 3) before building if the data changed.

## Full pipeline, in order

```bash
uv sync --all-extras
uv run python experiments/run_experiment.py experiments/configs/exp001_baseline01.yaml
# stage 2: run all scripts/paper/*.py  (see loop above)
uv run python scripts/paper/sync_paper_artifacts.py
# stage 4: execute the three notebooks (see loop above)
bash paper/build.sh all
```
