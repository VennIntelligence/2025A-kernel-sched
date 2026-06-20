"""Standard list schedulers and synthetic DAG helpers for CGO experiments.

All order generators in this file are structure-agnostic: they use only node
operation type, pipe/cycle metadata, buffer sizes/cache types, and DAG edges.
They never inspect case names or benchmark motifs.
"""

from __future__ import annotations

import random
import signal
from collections import defaultdict
from contextlib import contextmanager
from typing import Any

import harness as H

from ks_core.evaluator import compute_total_time

BASE_CANDIDATES = ("capfit_id", "p1", "id_raw")
ASSIGN_FALLBACKS = (
    ("far_only", 80),
    ("far_only", 120),
    ("size_only", 80),
    ("dist_size_cost", 120),
)


class AssignTimeout(RuntimeError):
    """Raised when the frozen assignment engine does not return promptly."""


@contextmanager
def _time_limit(seconds: int):
    if seconds <= 0:
        yield
        return

    def handler(_signum, _frame):
        raise AssignTimeout(f"assign timed out after {seconds}s")

    previous = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def safe_assign(
    inst,
    order: list[int],
    victim_policy: str = "dist_size_cost",
    prefetch_window: int = 0,
    timeout_seconds: int = 25,
) -> tuple[list[int], dict[int, int], list[tuple[int, int]], dict[str, Any]]:
    """Run the frozen assign engine, falling back only for engine failures.

    The first attempt is the caller-specified primary policy/window. Fallbacks
    preserve deterministic execution and use the same frozen assign
    implementation, but they are reported by callers because they are not part
    of the ideal control.
    """
    attempts = []
    for attempt in [(victim_policy, prefetch_window)] + list(ASSIGN_FALLBACKS):
        if attempt not in attempts:
            attempts.append(attempt)
    errors: list[str] = []
    for index, (policy, window) in enumerate(attempts):
        try:
            with _time_limit(timeout_seconds):
                order_ws, memory, spills = H.assign(
                    inst,
                    order,
                    victim_policy=policy,
                    prefetch_window=window,
                )
            meta = {
                "victim_policy": policy,
                "prefetch_window": window,
                "fallback": index > 0,
                "errors": errors,
            }
            return order_ws, memory, spills, meta
        except (RuntimeError, AssignTimeout) as exc:
            errors.append(f"{policy}/{window}: {type(exc).__name__}: {exc}")
            continue
    raise RuntimeError("; ".join(errors))


def controlled_total_time(
    inst,
    order_with_spills: list[int],
    memory: dict[int, int],
    spills: list[tuple[int, int]],
    spill_threshold: int = 5000,
) -> tuple[int, str]:
    """Compute time, avoiding byte-level address simulation for huge spill traces.

    ``pipeline_no_address`` keeps original/spill dependency and pipeline timing,
    but skips byte-level address-readiness constraints.
    """
    if len(spills) <= spill_threshold:
        return H.total_time(inst, order_with_spills, memory, spills), "address"
    nodes = {node.id: node for node in inst.nodes}
    time = compute_total_time(
        order_with_spills,
        nodes,
        inst.edges,
        memory=None,
        spill_entries=spills,
        num_original_nodes=len(inst.nodes),
    )
    return time, "pipeline_no_address"


def _graph(inst):
    nodes = {node.id: node for node in inst.nodes}
    successors: dict[int, list[int]] = defaultdict(list)
    predecessors: dict[int, list[int]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in nodes}
    for edge in inst.edges:
        if edge.src not in nodes or edge.dst not in nodes:
            continue
        successors[edge.src].append(edge.dst)
        predecessors[edge.dst].append(edge.src)
        indegree[edge.dst] += 1
    for values in successors.values():
        values.sort()
    for values in predecessors.values():
        values.sort()
    return nodes, successors, predecessors, indegree


def validate_topological_order(inst, order: list[int]) -> tuple[bool, str]:
    node_ids = {node.id for node in inst.nodes}
    if len(order) != len(inst.nodes):
        return False, f"length {len(order)} != {len(inst.nodes)}"
    if set(order) != node_ids:
        missing = sorted(node_ids - set(order))[:10]
        unknown = sorted(set(order) - node_ids)[:10]
        return False, f"node set mismatch missing={missing} unknown={unknown}"
    if len(set(order)) != len(order):
        return False, "duplicate node ids"
    pos = {node_id: index for index, node_id in enumerate(order)}
    for edge in inst.edges:
        if edge.src in pos and edge.dst in pos and pos[edge.src] >= pos[edge.dst]:
            return False, f"edge order violation {edge.src}->{edge.dst}"
    return True, ""


def _min_id_topological_order(inst) -> list[int]:
    nodes, successors, _predecessors, indegree = _graph(inst)
    ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    order: list[int] = []
    while ready:
        node_id = ready.pop(0)
        order.append(node_id)
        for dst in successors[node_id]:
            indegree[dst] -= 1
            if indegree[dst] == 0:
                ready.append(dst)
                ready.sort()
    if len(order) != len(nodes):
        raise ValueError("Input graph is not a DAG")
    return order


def _critical_path(inst) -> dict[int, int]:
    nodes, successors, _predecessors, _indegree = _graph(inst)
    topo = _min_id_topological_order(inst)
    cp: dict[int, int] = {}
    for node_id in reversed(topo):
        node = nodes[node_id]
        downstream = max((cp[dst] for dst in successors[node_id]), default=0)
        cp[node_id] = int(node.cycles or 0) + downstream
    return cp


def _alloc_by_buf(inst):
    return {
        node.buf_id: node
        for node in inst.nodes
        if node.op == "ALLOC" and node.buf_id is not None
    }


def _remaining_use_counts(inst) -> dict[int, int]:
    counts: dict[int, int] = defaultdict(int)
    for node in inst.nodes:
        if node.op in {"ALLOC", "FREE"}:
            continue
        for buf_id in node.bufs:
            counts[buf_id] += 1
    return counts


def _add_layered_ready(node_id: int, nodes, ready_free, ready_ops, ready_alloc) -> None:
    op = nodes[node_id].op
    if op == "FREE":
        ready_free.add(node_id)
    elif op == "ALLOC":
        ready_alloc.add(node_id)
    else:
        ready_ops.add(node_id)


def _update_live(current, node) -> None:
    if node.mem_type is None:
        return
    if node.op == "ALLOC":
        current[node.mem_type] += node.size
    elif node.op == "FREE":
        current[node.mem_type] = max(0, current[node.mem_type] - node.size)


def _release_bytes(node, alloc_by_buf, remaining_uses) -> int:
    return sum(
        alloc_by_buf[buf_id].size
        for buf_id in node.bufs
        if remaining_uses.get(buf_id, 0) == 1 and buf_id in alloc_by_buf
    )


def _finish_node(node, current, remaining_uses) -> None:
    _update_live(current, node)
    if node.op not in {"ALLOC", "FREE"}:
        for buf_id in node.bufs:
            if remaining_uses.get(buf_id, 0) > 0:
                remaining_uses[buf_id] -= 1


def cp_list(inst) -> list[int]:
    """Memory-unaware critical-path list scheduler."""
    nodes, successors, _predecessors, indegree = _graph(inst)
    cp = _critical_path(inst)
    ready = {node_id for node_id, degree in indegree.items() if degree == 0}
    order: list[int] = []

    while ready:
        node_id = min(ready, key=lambda candidate: (-cp[candidate], candidate))
        ready.remove(node_id)
        order.append(node_id)
        for dst in successors[node_id]:
            indegree[dst] -= 1
            if indegree[dst] == 0:
                ready.add(dst)

    if len(order) != len(nodes):
        raise ValueError("Input graph is not a DAG")
    return order


def cp_free_first(inst) -> list[int]:
    """Allocator-friendly latency scheduler used as a cp_list companion.

    It releases buffers as soon as their FREE node becomes ready, keeps the
    same critical-path priority for real operation nodes, and delays ALLOC
    nodes until no FREE/op node is ready. Ready ALLOC nodes use deterministic id
    order rather than memory size or capacity. It is still size blind, clean/dirty
    blind, and cache-weight blind; its role is to show whether results depend
    on the pathological liveness created by a pure latency-only list order.
    """
    nodes, successors, _predecessors, indegree = _graph(inst)
    cp = _critical_path(inst)
    ready_free: set[int] = set()
    ready_ops: set[int] = set()
    ready_alloc: set[int] = set()
    order: list[int] = []

    for node_id, degree in indegree.items():
        if degree == 0:
            _add_layered_ready(node_id, nodes, ready_free, ready_ops, ready_alloc)

    while ready_free or ready_ops or ready_alloc:
        if ready_free:
            node_id = min(ready_free, key=lambda nid: (-cp[nid], nid))
            ready_free.remove(node_id)
        elif ready_ops:
            node_id = min(ready_ops, key=lambda nid: (-cp[nid], nid))
            ready_ops.remove(node_id)
        else:
            node_id = min(ready_alloc)
            ready_alloc.remove(node_id)

        order.append(node_id)
        for dst in successors[node_id]:
            indegree[dst] -= 1
            if indegree[dst] == 0:
                _add_layered_ready(dst, nodes, ready_free, ready_ops, ready_alloc)

    if len(order) != len(nodes):
        raise ValueError("Input graph is not a DAG")
    return order


def pressure_uniform(inst) -> list[int]:
    """Uniform-byte pressure-aware list scheduler.

    The priority is intentionally clean/dirty-blind and cache-weight-blind.
    """
    nodes, successors, _predecessors, indegree = _graph(inst)
    alloc_by_buf = _alloc_by_buf(inst)
    remaining_uses = _remaining_use_counts(inst)
    current: dict[str, int] = defaultdict(int)
    ready_free: set[int] = set()
    ready_ops: set[int] = set()
    ready_alloc: set[int] = set()
    order: list[int] = []

    for node_id, degree in indegree.items():
        if degree == 0:
            _add_layered_ready(node_id, nodes, ready_free, ready_ops, ready_alloc)

    while ready_free or ready_ops or ready_alloc:
        if ready_free:
            node_id = min(ready_free, key=lambda nid: (-nodes[nid].size, nid))
            ready_free.remove(node_id)
        elif ready_ops:
            node_id = min(
                ready_ops,
                key=lambda nid: (
                    -_release_bytes(nodes[nid], alloc_by_buf, remaining_uses),
                    -int(nodes[nid].cycles or 0),
                    nid,
                ),
            )
            ready_ops.remove(node_id)
        else:
            node_id = min(ready_alloc, key=lambda nid: (nodes[nid].size, nid))
            ready_alloc.remove(node_id)

        node = nodes[node_id]
        order.append(node_id)
        _finish_node(node, current, remaining_uses)
        for dst in successors[node_id]:
            indegree[dst] -= 1
            if indegree[dst] == 0:
                _add_layered_ready(dst, nodes, ready_free, ready_ops, ready_alloc)

    if len(order) != len(nodes):
        raise ValueError("Input graph is not a DAG")
    return order


def goodman_hsu(inst) -> list[int]:
    """Goodman-Hsu-style latency/pressure mode switching scheduler."""
    nodes, successors, _predecessors, indegree = _graph(inst)
    cp = _critical_path(inst)
    alloc_by_buf = _alloc_by_buf(inst)
    remaining_uses = _remaining_use_counts(inst)
    current: dict[str, int] = defaultdict(int)
    ready = {node_id for node_id, degree in indegree.items() if degree == 0}
    order: list[int] = []

    def pressure_mode() -> bool:
        return any(current[cache] >= capacity for cache, capacity in H.CAP.items())

    while ready:
        if pressure_mode():
            free_ready = [node_id for node_id in ready if nodes[node_id].op == "FREE"]
            op_ready = [
                node_id
                for node_id in ready
                if nodes[node_id].op not in {"ALLOC", "FREE"}
            ]
            if free_ready:
                node_id = min(free_ready, key=lambda nid: (-nodes[nid].size, nid))
            elif op_ready:
                node_id = min(
                    op_ready,
                    key=lambda nid: (
                        -_release_bytes(nodes[nid], alloc_by_buf, remaining_uses),
                        -int(nodes[nid].cycles or 0),
                        nid,
                    ),
                )
            else:
                node_id = min(ready, key=lambda nid: (nodes[nid].size, nid))
        else:
            node_id = min(ready, key=lambda nid: (-cp[nid], nid))

        ready.remove(node_id)
        node = nodes[node_id]
        order.append(node_id)
        _finish_node(node, current, remaining_uses)
        for dst in successors[node_id]:
            indegree[dst] -= 1
            if indegree[dst] == 0:
                ready.add(dst)

    if len(order) != len(nodes):
        raise ValueError("Input graph is not a DAG")
    return order


def p1_official_key(order: list[int], time: int, inst) -> tuple[int, int, int, int, int, int]:
    nodes = {node.id: node for node in inst.nodes}
    live = {cache: 0 for cache in H.CAP}
    peak = {cache: 0 for cache in H.CAP}
    counts = {"L0A": 0, "L0B": 0, "L0C": 0}
    peak_counts = {"L0A": 0, "L0B": 0, "L0C": 0}
    for node_id in order:
        node = nodes[node_id]
        if node.mem_type is None:
            continue
        if node.op == "ALLOC":
            live[node.mem_type] += node.size
            peak[node.mem_type] = max(peak[node.mem_type], live[node.mem_type])
            if node.mem_type in counts:
                counts[node.mem_type] += 1
                peak_counts[node.mem_type] = max(peak_counts[node.mem_type], counts[node.mem_type])
        elif node.op == "FREE":
            live[node.mem_type] = max(0, live[node.mem_type] - node.size)
            if node.mem_type in counts:
                counts[node.mem_type] = max(0, counts[node.mem_type] - 1)
    return (
        peak["L1"],
        peak["UB"],
        peak_counts["L0A"],
        peak_counts["L0B"],
        peak_counts["L0C"],
        time,
    )


def select_ours_order(inst) -> dict[str, Any]:
    """Replicate the promoted portfolio selection without returning spill ids as a base order."""
    best: dict[str, Any] | None = None
    if inst.problem_id == 1:
        windows = (0,)
    elif inst.problem_id >= 3:
        windows = (0, 5, 40, 80, 120)
    else:
        windows = (0, 5, 40)

    for base_name in BASE_CANDIDATES:
        base_order = H.build_order(inst, base_name)
        ok, reason = validate_topological_order(inst, base_order)
        if not ok:
            raise ValueError(f"ours candidate {base_name} invalid: {reason}")
        for window in windows:
            order_ws, memory, spills, assign_meta = safe_assign(
                inst,
                base_order,
                victim_policy="dist_size_cost",
                prefetch_window=window,
            )
            split = H.extra_split(spills, inst)
            time, time_source = controlled_total_time(inst, order_ws, memory, spills)
            if inst.problem_id == 1:
                key = p1_official_key(base_order, time, inst)
            elif inst.problem_id >= 3:
                key = (time, split["extra"], split["spills"])
            else:
                key = (split["extra"], split["spills"], time)
            record = {
                "key": key,
                "selected_base": base_name,
                "requested_prefetch_window": window,
                "prefetch_window": assign_meta["prefetch_window"],
                "victim_policy": assign_meta["victim_policy"],
                "assign_meta": assign_meta,
                "time_source": time_source,
                "base_order": list(base_order),
                "order_with_spills": order_ws,
                "memory": memory,
                "spills": spills,
                "split": split,
                "time": time,
            }
            if best is None or key < best["key"]:
                best = record
    if best is None:
        raise RuntimeError("no ours portfolio candidate evaluated")
    return best


def _aligned(value: int, quantum: int = 16) -> int:
    return max(quantum, ((value + quantum - 1) // quantum) * quantum)


def _default_sizes(capacity: int, n_reserve: int, regime: str) -> tuple[int, int]:
    if regime == "capacity_bound":
        reserve = _aligned(capacity // max(2, n_reserve - 1) + 1)
        while reserve * n_reserve <= capacity:
            reserve += 16
    else:
        reserve = _aligned(capacity // max(4, n_reserve + 2))
    reserve = min(reserve, capacity - 16)
    temp = min(_aligned(max(16, reserve // 2)), max(16, capacity - reserve))
    return reserve, temp


def gen_instance(seed: int, knobs: dict[str, Any]) -> dict[str, Any]:
    """Generate a deterministic synthetic DAG.

    Knobs:
      target_cache: one of L1/UB/L0C
      regime: capacity_bound or order_reachable
      n_reserve: number of long-lived reserve buffers
      n_acc: number of compute steps
      dirty_reserve: if true reserve buffers are compute-produced, not COPY_IN
      reserve_size/temp_size: optional byte sizes
    """
    rng = random.Random(seed)
    target_cache = str(knobs.get("target_cache", "UB"))
    if target_cache not in H.CAP:
        raise ValueError(f"unknown target_cache {target_cache}")
    regime = str(knobs.get("regime", "capacity_bound"))
    if regime not in {"capacity_bound", "order_reachable"}:
        raise ValueError(f"unknown regime {regime}")
    n_reserve = int(knobs.get("n_reserve", 5))
    n_acc = int(knobs.get("n_acc", 4))
    dirty_reserve = bool(knobs.get("dirty_reserve", False))
    reserve_size, temp_size = _default_sizes(H.CAP[target_cache], n_reserve, regime)
    reserve_size = int(knobs.get("reserve_size", reserve_size))
    temp_size = int(knobs.get("temp_size", temp_size))
    if reserve_size + temp_size > H.CAP[target_cache]:
        temp_size = max(16, H.CAP[target_cache] - reserve_size)

    nodes: list[dict[str, Any]] = []
    edges: list[list[int]] = []
    next_node_id = 0
    next_buf_id = 0

    def new_node(data: dict[str, Any]) -> int:
        nonlocal next_node_id
        data["Id"] = next_node_id
        nodes.append(data)
        next_node_id += 1
        return data["Id"]

    def new_buf() -> int:
        nonlocal next_buf_id
        buf_id = next_buf_id
        next_buf_id += 1
        return buf_id

    def alloc(buf_id: int, size: int, mem_type: str) -> int:
        return new_node({"Op": "ALLOC", "BufId": buf_id, "Size": size, "Type": mem_type})

    def free(buf_id: int, size: int, mem_type: str) -> int:
        return new_node({"Op": "FREE", "BufId": buf_id, "Size": size, "Type": mem_type})

    def copy_in(buf_id: int) -> int:
        return new_node({"Op": "COPY_IN", "Bufs": [buf_id], "Cycles": 20, "Pipe": "MTE2"})

    def op(name: str, bufs: list[int], cycles: int, pipe: str) -> int:
        return new_node({"Op": name, "Bufs": list(bufs), "Cycles": cycles, "Pipe": pipe})

    reserve: list[dict[str, Any]] = []
    for _ in range(n_reserve):
        buf_id = new_buf()
        alloc_id = alloc(buf_id, reserve_size, target_cache)
        if dirty_reserve:
            ready_id = op("VEC", [buf_id], 25 + rng.randrange(10), "VECTOR")
        else:
            ready_id = copy_in(buf_id)
        edges.append([alloc_id, ready_id])
        reserve.append({"buf": buf_id, "alloc": alloc_id, "ready": ready_id, "uses": []})

    compute_nodes: list[int] = []
    previous_compute: int | None = None
    for index in range(n_acc):
        temp_buf = new_buf()
        temp_alloc = alloc(temp_buf, temp_size, target_cache)
        temp_ready = copy_in(temp_buf)
        chosen = reserve[index % n_reserve]
        compute = op("MATMUL", [chosen["buf"], temp_buf], 60 + rng.randrange(30), "CUBE")
        temp_free = free(temp_buf, temp_size, target_cache)
        edges.extend(
            [
                [temp_alloc, temp_ready],
                [temp_ready, compute],
                [chosen["ready"], compute],
                [compute, temp_free],
                [temp_ready, temp_free],
                [temp_alloc, temp_free],
            ]
        )
        if previous_compute is not None:
            edges.append([previous_compute, compute])
        previous_compute = compute
        compute_nodes.append(compute)
        chosen["uses"].append(compute)

    if regime == "capacity_bound":
        barrier = op("BARRIER", [], 1, "VECTOR")
        for item in reserve:
            edges.append([item["ready"], barrier])
        for compute in compute_nodes:
            edges.append([compute, barrier])
        for item in reserve:
            free_id = free(item["buf"], reserve_size, target_cache)
            edges.extend([[item["alloc"], free_id], [item["ready"], free_id], [barrier, free_id]])
            for use_id in item["uses"]:
                edges.append([use_id, free_id])
    else:
        for item in reserve:
            free_id = free(item["buf"], reserve_size, target_cache)
            edges.extend([[item["alloc"], free_id], [item["ready"], free_id]])
            for use_id in item["uses"]:
                edges.append([use_id, free_id])

    return {"Nodes": nodes, "Edges": edges}


def overflow_area(order: list[int], inst) -> int:
    nodes = {node.id: node for node in inst.nodes}
    current: dict[str, int] = defaultdict(int)
    total = 0
    for node_id in order:
        node = nodes[node_id]
        if node.mem_type is not None:
            if node.op == "ALLOC":
                current[node.mem_type] += node.size
            elif node.op == "FREE":
                current[node.mem_type] = max(0, current[node.mem_type] - node.size)
        for cache, capacity in H.CAP.items():
            total += max(0, current[cache] - capacity)
    return total


def overflow_lower_bound(order: list[int], inst, cache: str) -> int:
    nodes = {node.id: node for node in inst.nodes}
    current = 0
    peak_over = 0
    for node_id in order:
        node = nodes[node_id]
        if node.mem_type == cache:
            if node.op == "ALLOC":
                current += node.size
            elif node.op == "FREE":
                current = max(0, current - node.size)
        peak_over = max(peak_over, current - H.CAP[cache])
    return max(0, peak_over)
