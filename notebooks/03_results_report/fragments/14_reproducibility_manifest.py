# %% [markdown]
# ## 13. Reproducibility manifest
#
# Numbers in this report come from `results/paper/*.csv`; paper figures come
# from `output/02_paper_figures/*.png`; paper-ready copies are synced into
# `paper/assets/` by `scripts/paper/sync_paper_artifacts.py`.

# %%
artifacts = pd.DataFrame(
    [
        {"artifact": "final solver", "path": "src/ks_core/solver.py"},
        {"artifact": "method entry point", "path": "algorithms/ours/solve.py"},
        {"artifact": "best iteration marker", "path": "autoresearch/best_iter.txt"},
        {"artifact": "paper CSV manifest", "path": "results/paper/MANIFEST.md"},
        {"artifact": "paper number manifest", "path": "results/paper/PAPER_NUMBERS.yml"},
        {"artifact": "paper figures", "path": "output/02_paper_figures/"},
        {"artifact": "paper sync script", "path": "scripts/paper/sync_paper_artifacts.py"},
        {"artifact": "this notebook source", "path": "notebooks/03_results_report/fragments/"},
    ]
)
display(artifacts)

commands = pd.DataFrame(
    [
        {"task": "regenerate paper data", "command": "uv run python scripts/paper/inv_inventory.py && uv run python scripts/paper/prob_metrics.py"},
        {"task": "build data & problem", "command": "uv run python scripts/build_notebook.py notebooks/01_data_and_problem --execute"},
        {"task": "build paper figures", "command": "uv run python scripts/build_notebook.py notebooks/02_paper_figures --execute"},
        {"task": "build this report", "command": "uv run python scripts/build_notebook.py notebooks/03_results_report --execute"},
        {"task": "sync paper artifacts", "command": "uv run python scripts/paper/sync_paper_artifacts.py"},
        {"task": "run tests", "command": "uv run pytest -v"},
    ]
)
display(commands)

note(
    "The notebook suite is three reports: `01_data_and_problem` (data + problem "
    "framing), `02_paper_figures` (the paper-figure factory), and this "
    "`03_results_report` (evidence narrative). All read `results/paper/*.csv`."
)
