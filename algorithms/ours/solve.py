"""Promoted "ours" solver — the ``algorithms.<name>`` entry point.

The implementation is the single source of truth in :mod:`ks_core.solver`;
this module only re-exports it so ``experiments/run_experiment.py`` can load it
as ``algorithms.ours.solve``.  Post-review v2 evidence is stored under
``../../results/autoresearch_v2``.
"""

from ks_core.solver import solve

__all__ = ["solve"]
