"""E14 -- CP-SAT oracle for small synthetic DAGs."""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import baselines as B
import harness as H
from ortools.sat.python import cp_model

from ks_core.evaluator import validate_memory, validate_spill
from ks_core.graph import load_json

ROOT = Path(__file__).resolve().parents[2]
ORACLE_DIR = ROOT / "data" / "processed" / "synthetic" / "oracle"
RESULTS = ROOT / "results" / "paper"
OUT = RESULTS / "e14_oracle.csv"
MANIFEST = ORACLE_DIR / "manifest.csv"
ORACLE_SIZE = 8

MANIFEST_FIELDS = [
    "inst_id",
    "seed",
    "target_cache",
    "n_nodes",
    "n_edges",
    "dirty_reserve",
    "min_peak_target_over_cap",
    "regime",
    "bound_cache",
]
OUT_FIELDS = [
    "inst_id",
    "n_nodes",
    "bound_cache",
    "capacity",
    "W_star_bound",
    "ratio_Wstar",
    "ours_real_extra",
    "ours_order_extra_caponly",
    "lb_T1",
    "A_ours",
    "ratio_E_over_A",
    "Estar_joint",
    "joint_status",
    "gap_real_vs_joint",
    "gap_real_vs_fixed",
]


def _validate_instance(inst) -> list[str]:
    order = H.build_order(inst, "capfit_id")
    order_ws, memory, spills = H.assign(
        inst,
        order,
        victim_policy="dist_size_cost",
        prefetch_window=0,
    )
    nodes = {node.id: node for node in inst.nodes}
    errors = validate_memory(
        order_ws,
        nodes,
        memory,
        spill_entries=spills,
        num_original_nodes=len(inst.nodes),
    )
    errors += validate_spill(order_ws, nodes, inst.edges, spills, len(inst.nodes))
    return errors


def _generate_oracle_inputs() -> list[dict[str, Any]]:
    ORACLE_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    attempts = 0
    while len(rows) < ORACLE_SIZE and attempts < ORACLE_SIZE * 10:
        attempts += 1
        seed = 9100 + attempts
        bound_cache = ("UB", "L0C")[attempts % 2]
        knobs = {
            "target_cache": bound_cache,
            "regime": "capacity_bound",
            "n_reserve": 4,
            "n_acc": 1,
            "dirty_reserve": bool((attempts // 2) % 2),
        }
        data = B.gen_instance(seed, knobs)
        if len(data["Nodes"]) > 30:
            continue
        tmp_path = ORACLE_DIR / "_candidate.json"
        tmp_path.write_text(json.dumps(data), encoding="utf-8")
        inst = load_json(tmp_path, problem_id=2)
        errors = _validate_instance(inst)
        if errors:
            continue
        ratio, regime = _scan_regime(inst, bound_cache, seed)
        inst_id = f"oracle_{len(rows):03d}"
        out_path = ORACLE_DIR / f"{inst_id}.json"
        out_path.write_text(json.dumps(data), encoding="utf-8")
        rows.append(
            {
                "inst_id": inst_id,
                "seed": seed,
                "target_cache": bound_cache,
                "n_nodes": len(data["Nodes"]),
                "n_edges": len(data["Edges"]),
                "dirty_reserve": knobs["dirty_reserve"],
                "min_peak_target_over_cap": f"{ratio:.8g}",
                "regime": regime,
                "bound_cache": bound_cache,
            }
        )
    candidate = ORACLE_DIR / "_candidate.json"
    if candidate.exists():
        candidate.unlink()
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def _scan_regime(inst, bound_cache: str, seed: int) -> tuple[float, str]:
    candidates = [B.cp_list(inst), B.pressure_uniform(inst), B.goodman_hsu(inst)]
    for offset in range(16):
        candidates.append(H.random_topo(inst, seed * 1000 + offset))
    min_peak = min(H.peak_working_set(order, inst).get(bound_cache, 0) for order in candidates)
    ratio = min_peak / H.CAP[bound_cache]
    return ratio, "capacity_bound" if ratio > 1.0 else "order_reachable"


def _buffer_info(inst) -> dict[int, dict[str, Any]]:
    allocs = {
        node.buf_id: node
        for node in inst.nodes
        if node.op == "ALLOC" and node.buf_id is not None
    }
    frees = {
        node.buf_id: node
        for node in inst.nodes
        if node.op == "FREE" and node.buf_id is not None
    }
    users: dict[int, list[int]] = defaultdict(list)
    for node in inst.nodes:
        if node.op in {"ALLOC", "FREE"}:
            continue
        for buf_id in node.bufs:
            if buf_id in allocs:
                users[buf_id].append(node.id)
    clean = H.clean_bufs(inst)
    info = {}
    for buf_id, alloc in allocs.items():
        if buf_id not in frees:
            raise ValueError(f"buffer {buf_id} has no FREE")
        info[buf_id] = {
            "alloc": alloc.id,
            "free": frees[buf_id].id,
            "users": users.get(buf_id, []),
            "size": alloc.size,
            "mem_type": alloc.mem_type,
            "clean": buf_id in clean,
            "cost": alloc.size if buf_id in clean else 2 * alloc.size,
        }
    return info


def _solve_m1_peak(inst, bound_cache: str, max_seconds: float = 20.0) -> dict[str, Any]:
    nodes = [node.id for node in inst.nodes]
    n = len(nodes)
    model = cp_model.CpModel()
    x = {
        (node_id, slot): model.NewBoolVar(f"x_{node_id}_{slot}")
        for node_id in nodes
        for slot in range(n)
    }
    pos = {
        node_id: model.NewIntVar(0, n - 1, f"pos_{node_id}")
        for node_id in nodes
    }
    for node_id in nodes:
        model.Add(sum(x[(node_id, slot)] for slot in range(n)) == 1)
        model.Add(pos[node_id] == sum(slot * x[(node_id, slot)] for slot in range(n)))
    for slot in range(n):
        model.Add(sum(x[(node_id, slot)] for node_id in nodes) == 1)
    node_set = set(nodes)
    for edge in inst.edges:
        if edge.src in node_set and edge.dst in node_set:
            model.Add(pos[edge.src] + 1 <= pos[edge.dst])

    buffers = _buffer_info(inst)
    max_by_cache = {
        cache: sum(info["size"] for info in buffers.values() if info["mem_type"] == cache)
        for cache in H.CAP
    }
    peak = {
        cache: model.NewIntVar(0, max_by_cache[cache], f"peak_{cache}")
        for cache in H.CAP
    }
    for cache in H.CAP:
        for slot in range(n):
            terms = []
            for info in buffers.values():
                if info["mem_type"] != cache:
                    continue
                alloc_prefix = sum(x[(info["alloc"], prefix)] for prefix in range(slot + 1))
                free_prefix = sum(x[(info["free"], prefix)] for prefix in range(slot + 1))
                terms.append(info["size"] * (alloc_prefix - free_prefix))
            model.Add(peak[cache] >= sum(terms))

    model.Minimize(peak[bound_cache])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    status = solver.Solve(model)
    status_name = solver.StatusName(status)
    result: dict[str, Any] = {"status": status_name, "objective": None, "order": None, "peaks": {}}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        order = sorted(nodes, key=lambda node_id: solver.Value(pos[node_id]))
        result.update(
            {
                "objective": int(solver.ObjectiveValue()),
                "order": order,
                "peaks": {cache: int(solver.Value(var)) for cache, var in peak.items()},
            }
        )
    return result


def _solve_m2_fixed(inst, order: list[int], max_seconds: float = 10.0) -> dict[str, Any]:
    n = len(order)
    pos = {node_id: index for index, node_id in enumerate(order)}
    buffers = _buffer_info(inst)
    model = cp_model.CpModel()
    resident: dict[tuple[int, int], Any] = {}
    objective_terms = []

    for buf_id, info in buffers.items():
        alloc_pos = pos[info["alloc"]]
        free_pos = pos[info["free"]]
        if alloc_pos > free_pos:
            raise ValueError(f"buffer {buf_id} ALLOC after FREE")
        for slot in range(alloc_pos, free_pos + 1):
            resident[(buf_id, slot)] = model.NewBoolVar(f"res_{buf_id}_{slot}")
        model.Add(resident[(buf_id, alloc_pos)] == 1)
        model.Add(resident[(buf_id, free_pos)] == 1)
        for user_id in info["users"]:
            model.Add(resident[(buf_id, pos[user_id])] == 1)
        for slot in range(alloc_pos + 1, free_pos + 1):
            reload = model.NewBoolVar(f"reload_{buf_id}_{slot}")
            model.Add(reload >= resident[(buf_id, slot)] - resident[(buf_id, slot - 1)])
            objective_terms.append(info["cost"] * reload)

    for slot in range(n):
        for cache, capacity in H.CAP.items():
            terms = []
            for buf_id, info in buffers.items():
                key = (buf_id, slot)
                if info["mem_type"] == cache and key in resident:
                    terms.append(info["size"] * resident[key])
            model.Add(sum(terms) <= capacity)

    model.Minimize(sum(objective_terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    status = solver.Solve(model)
    status_name = solver.StatusName(status)
    result: dict[str, Any] = {"status": status_name, "objective": None, "best_bound": None}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result["objective"] = int(solver.ObjectiveValue())
        result["best_bound"] = int(solver.BestObjectiveBound())
    return result


def _ratio(num: int | float | None, den: int | float | None) -> str:
    if num is None or den is None or den == 0:
        return ""
    return f"{float(num) / float(den):.8g}"


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    manifest_rows = _generate_oracle_inputs()
    assertion_failures: list[str] = []
    output_rows: list[dict[str, Any]] = []
    fixed_gaps: list[float] = []
    e_over_a_values: list[float] = []
    capacity_bound_count = 0

    if len(manifest_rows) < ORACLE_SIZE:
        assertion_failures.append(f"oracle suite size {len(manifest_rows)} < {ORACLE_SIZE}")

    for item in manifest_rows:
        print(f"E14 solve {item['inst_id']} ({item['bound_cache']})", flush=True)
        path = ORACLE_DIR / f"{item['inst_id']}.json"
        inst = load_json(path, problem_id=2)
        bound_cache = item["bound_cache"]
        capacity = H.CAP[bound_cache]
        m1 = _solve_m1_peak(inst, bound_cache)
        print(f"E14 {item['inst_id']} M1 {m1['status']} {m1['objective']}", flush=True)
        if m1["status"] != "OPTIMAL":
            assertion_failures.append(f"{item['inst_id']}: M1 status {m1['status']}")
        w_star = m1["objective"]
        ratio_wstar = (w_star / capacity) if w_star is not None else None
        if ratio_wstar is not None and ratio_wstar > 1.0:
            capacity_bound_count += 1
        else:
            assertion_failures.append(
                f"{item['inst_id']}: expected ratio_Wstar > 1 for {bound_cache}, got {ratio_wstar}"
            )

        ours = B.select_ours_order(inst)
        ours_order = ours["base_order"]
        ours_real_extra = int(ours["split"]["extra"])
        ours_fixed = _solve_m2_fixed(inst, ours_order)
        print(
            f"E14 {item['inst_id']} M2 ours {ours_fixed['status']} "
            f"{ours_fixed['objective']}",
            flush=True,
        )
        cp_fixed = _solve_m2_fixed(inst, B.cp_list(inst))
        m1_fixed = _solve_m2_fixed(inst, m1["order"]) if m1["order"] is not None else None

        if ours_fixed["status"] != "OPTIMAL":
            assertion_failures.append(
                f"{item['inst_id']}: ours fixed M2 status {ours_fixed['status']}"
            )
        if cp_fixed["status"] != "OPTIMAL":
            assertion_failures.append(
                f"{item['inst_id']}: cp_list fixed M2 status {cp_fixed['status']}"
            )
        if m1_fixed is not None and m1_fixed["status"] != "OPTIMAL":
            assertion_failures.append(
                f"{item['inst_id']}: M1-order fixed M2 status {m1_fixed['status']}"
            )

        fixed_extra = ours_fixed["objective"]
        lb_t1 = B.overflow_lower_bound(ours_order, inst, bound_cache)
        area = B.overflow_area(ours_order, inst)
        if fixed_extra is not None and fixed_extra < lb_t1:
            assertion_failures.append(
                f"{item['inst_id']}: Estar_fixed {fixed_extra} < lb_T1 {lb_t1}"
            )
        if fixed_extra is not None and ours_real_extra < fixed_extra:
            assertion_failures.append(
                f"{item['inst_id']}: real extra {ours_real_extra} < fixed cap-only {fixed_extra}"
            )

        # M3 is intentionally skipped; if implemented later, assert it is no
        # worse than every fixed-order optimum.
        joint_status = "SKIPPED"
        estar_joint = None

        if fixed_extra is not None and fixed_extra > 0:
            fixed_gaps.append(ours_real_extra / fixed_extra)
        if fixed_extra is not None and area > 0:
            e_over_a_values.append(fixed_extra / area)

        output_rows.append(
            {
                "inst_id": item["inst_id"],
                "n_nodes": len(inst.nodes),
                "bound_cache": bound_cache,
                "capacity": capacity,
                "W_star_bound": "" if w_star is None else w_star,
                "ratio_Wstar": "" if ratio_wstar is None else f"{ratio_wstar:.8g}",
                "ours_real_extra": ours_real_extra,
                "ours_order_extra_caponly": "" if fixed_extra is None else fixed_extra,
                "lb_T1": lb_t1,
                "A_ours": area,
                "ratio_E_over_A": _ratio(fixed_extra, area),
                "Estar_joint": "" if estar_joint is None else estar_joint,
                "joint_status": joint_status,
                "gap_real_vs_joint": _ratio(ours_real_extra, estar_joint),
                "gap_real_vs_fixed": _ratio(ours_real_extra, fixed_extra),
            }
        )

    if capacity_bound_count < 1:
        assertion_failures.append("expected at least one ratio_Wstar > 1 graph")

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUT_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    if fixed_gaps:
        print(f"gap_real_vs_fixed median={statistics.median(fixed_gaps):.8g}")
    else:
        print("gap_real_vs_fixed median=")
    print("gap_real_vs_joint median=SKIPPED")
    if e_over_a_values:
        print(
            "ratio_E_over_A range="
            f"{min(e_over_a_values):.8g}..{max(e_over_a_values):.8g}"
        )
    else:
        print("ratio_E_over_A range=")

    for failure in assertion_failures:
        print(f"ASSERTION FAILED E14: {failure}")
    if assertion_failures:
        raise SystemExit(1)

    print(
        f"DONE E14: {ORACLE_DIR.relative_to(ROOT)}/ ({len(manifest_rows)} instances), "
        f"{OUT.relative_to(ROOT)} (M3 joint_status=SKIPPED)"
    )


if __name__ == "__main__":
    main()
