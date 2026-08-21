"""Regression tests for the post-review solver changes."""

from __future__ import annotations

from pathlib import Path

from ks_core import solver
from ks_core.graph import load_json
from ks_core.metrics import collect_validation_errors

ROOT = Path(__file__).resolve().parents[1]


def test_free_space_find_is_true_best_fit() -> None:
    space = solver._FreeSpace(100)
    space.free = [(0, 80), (80, 20)]

    assert space.find(16) == 80


def test_unlock_frontier_is_a_valid_topological_order() -> None:
    instance = load_json(
        ROOT / "data" / "processed" / "synthetic" / "oracle" / "oracle_000.json",
        problem_id=1,
    )

    order = solver._unlock_frontier_order(instance)

    assert collect_validation_errors(instance, order) == []
