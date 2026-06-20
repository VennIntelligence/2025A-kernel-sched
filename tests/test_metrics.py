"""Unit tests for the unified metrics evaluation API."""

from __future__ import annotations

import json
from pathlib import Path

from ks_core.evaluator import compute_max_vstay, validate_memory
from ks_core.metrics import (
    CANONICAL_METRIC_KEYS,
    compare_experiments,
    evaluate,
    evaluation_to_metrics,
    load_metrics,
)
from ks_core.types import Edge, Node, ProblemInstance


def _alloc(node_id: int, buf_id: int, size: int, mem_type: str = "L1") -> Node:
    return Node(
        id=node_id,
        op="ALLOC",
        buf_id=buf_id,
        size=size,
        mem_type=mem_type,
        cycles=0,
    )


def _free(node_id: int, buf_id: int, size: int, mem_type: str = "L1") -> Node:
    return Node(
        id=node_id,
        op="FREE",
        buf_id=buf_id,
        size=size,
        mem_type=mem_type,
        cycles=0,
    )


def _op(node_id: int, pipe: str = "CUBE", cycles: int = 10, bufs: list[int] | None = None) -> Node:
    return Node(id=node_id, op="CONV", pipe=pipe, cycles=cycles, bufs=bufs or [])


def test_compute_max_vstay_tracks_peak_residency():
    nodes = {
        0: _alloc(0, 1, 100),
        1: _free(1, 1, 100),
        2: _alloc(2, 2, 250),
        3: _free(3, 2, 250),
    }
    metrics = compute_max_vstay([0, 1, 2, 3], nodes)
    assert metrics["max_L1"] == 250


def test_evaluate_detects_dependency_violation():
    instance = ProblemInstance(
        case_name="tiny",
        problem_id=1,
        nodes=[_alloc(0, 1, 64), _op(1, bufs=[1]), _free(2, 1, 64)],
        edges=[Edge(src=0, dst=1), Edge(src=1, dst=2)],
    )
    result = evaluate(instance, [1, 0, 2])
    assert not result.valid
    assert any("Dependency violation" in error for error in result.errors)


def test_validate_memory_detects_overlapping_offsets():
    nodes = {
        0: _alloc(0, 1, 100),
        1: _alloc(1, 2, 100),
        2: _free(2, 1, 100),
        3: _free(3, 2, 100),
    }
    order = [0, 1, 2, 3]
    memory = {1: 0, 2: 50}
    errors = validate_memory(order, nodes, memory, num_original_nodes=4)
    assert errors
    assert any("overlap" in error for error in errors)


def test_evaluate_p2_spill_schedule_is_valid_for_minimal_case():
    instance = ProblemInstance(
        case_name="tiny",
        problem_id=2,
        nodes=[_alloc(0, 1, 64), _op(1, bufs=[1]), _free(2, 1, 64)],
        edges=[Edge(src=0, dst=1), Edge(src=1, dst=2)],
    )
    memory = {1: 0}
    spill_entries = [(1, 128)]
    order = [0, 1, 3, 4, 2]
    result = evaluate(instance, order, memory, spill_entries)
    assert result.valid
    assert result.metrics["spills"] == 1
    assert result.metrics["extra"] == 128
    assert set(result.metrics) >= set(CANONICAL_METRIC_KEYS)


def test_evaluate_p2_empty_memory_requires_offsets():
    instance = ProblemInstance(
        case_name="tiny",
        problem_id=2,
        nodes=[_alloc(0, 1, 64), _op(1, bufs=[1]), _free(2, 1, 64)],
        edges=[Edge(src=0, dst=1), Edge(src=1, dst=2)],
    )
    result = evaluate(instance, [0, 1, 2], memory={}, spill_entries=[])
    assert not result.valid
    assert any("Missing memory offsets" in error for error in result.errors)


def test_evaluate_p2_empty_spills_rejects_unknown_synthetic_node():
    instance = ProblemInstance(
        case_name="tiny",
        problem_id=2,
        nodes=[_alloc(0, 1, 64), _op(1, bufs=[1]), _free(2, 1, 64)],
        edges=[Edge(src=0, dst=1), Edge(src=1, dst=2)],
    )
    result = evaluate(instance, [0, 1, 3, 2], memory={1: 0}, spill_entries=[])
    assert not result.valid
    assert any("Unknown nodes" in error for error in result.errors)


def test_evaluate_p1_without_memory_remains_valid():
    instance = ProblemInstance(
        case_name="tiny",
        problem_id=1,
        nodes=[_alloc(0, 1, 64), _free(1, 1, 64)],
        edges=[Edge(src=0, dst=1)],
    )
    result = evaluate(instance, [0, 1])
    assert result.valid


def test_evaluation_to_metrics_maps_canonical_keys():
    instance = ProblemInstance(
        case_name="tiny",
        problem_id=1,
        nodes=[_alloc(0, 1, 64), _free(1, 1, 64)],
        edges=[Edge(src=0, dst=1)],
    )
    result = evaluate(instance, [0, 1])
    summary = evaluation_to_metrics(result)
    assert summary.total_time == result.metrics["time"]
    assert summary.schedule_length == result.metrics["schedule_len"]
    assert summary.violations == 0


def test_compare_experiments_flattens_list_metrics(tmp_path: Path):
    exp_a = tmp_path / "exp_a"
    exp_b = tmp_path / "exp_b"
    exp_a.mkdir()
    exp_b.mkdir()

    (exp_a / "metrics.json").write_text(
        json.dumps(
            [
                {"case": "Conv_Case0", "problem": 1, "time": 10, "valid": True},
                {"case": "Conv_Case1", "problem": 1, "time": 20, "valid": True},
            ]
        )
    )
    (exp_b / "metrics.json").write_text(
        json.dumps({"case": "Conv_Case0", "problem": 2, "time": 30, "valid": False})
    )

    rows = compare_experiments([exp_a, exp_b])
    assert len(rows) == 3
    assert {row["experiment"] for row in rows} == {"exp_a", "exp_b"}
    assert load_metrics(exp_a / "metrics.json")[0]["time"] == 10
