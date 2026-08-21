"""Temporary spill-aware order search for P2.

This prototype deliberately does not read baseline schedules or case names.  It
searches generic list-scheduler weights and scores every completed order with
the repository's concrete address assignment + canonical evaluator.

Examples
--------
uv run python scripts/agent_direct_search.py --cases Conv_Case0 FlashAttention_Case0 --trials 300
uv run python scripts/agent_direct_search.py --cases all --trials 20

See scripts/agent_direct_search.md for the full reproduction guide.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import random
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ortools.sat.python import cp_model  # noqa: E402

from ks_core import solver as core_solver  # noqa: E402
from ks_core.constants import CACHE_CAPACITIES  # noqa: E402
from ks_core.graph import load_json  # noqa: E402
from ks_core.metrics import evaluate  # noqa: E402

CASES = [
    "Conv_Case0",
    "Conv_Case1",
    "FlashAttention_Case0",
    "FlashAttention_Case1",
    "Matmul_Case0",
    "Matmul_Case1",
]


@dataclass(frozen=True)
class Weights:
    # ALLOC: lower score is chosen. Dynamic successor wait is intentionally
    # dominant in most seeds; remaining terms decide which wavefront to open.
    alloc_wait: float = 8.0
    alloc_pressure: float = 1.0
    alloc_dirty: float = 0.0
    alloc_users: float = 0.0
    alloc_id: float = 0.0
    alloc_depth: float = 0.0
    alloc_noise: float = 0.0
    # Ready operation: higher utility is chosen.
    op_release_dirty: float = 4.0
    op_release_clean: float = 2.0
    op_touched: float = 0.2
    op_unlock_free: float = 2.0
    op_unlock_op: float = 0.5
    op_id: float = 0.0
    op_noise: float = 0.0
    # 0 keeps the safe FREE > op > ALLOC regime. Positive values may admit an
    # ALLOC while operations are ready when it is close to unlocking work.
    interleave_threshold: float = 0.0
    # Logical occupancy throttle.  Zero disables it; one defers an ALLOC while
    # another ready allocation fits its cache.
    capacity_gate: float = 1.0


def _random_weights(rng: random.Random) -> Weights:
    def signed(scale: float) -> float:
        return rng.uniform(-scale, scale)

    return Weights(
        alloc_wait=10 ** rng.uniform(0.2, 1.5),
        alloc_pressure=10 ** rng.uniform(-1.2, 1.1),
        alloc_dirty=signed(3.0),
        alloc_users=signed(2.0),
        alloc_id=signed(2.5),
        alloc_depth=signed(2.5),
        alloc_noise=10 ** rng.uniform(-2.0, 0.5),
        op_release_dirty=10 ** rng.uniform(-0.2, 1.2),
        op_release_clean=10 ** rng.uniform(-0.4, 1.0),
        op_touched=10 ** rng.uniform(-1.5, 0.7),
        op_unlock_free=10 ** rng.uniform(-0.5, 1.0),
        op_unlock_op=10 ** rng.uniform(-1.0, 0.8),
        op_id=signed(1.5),
        op_noise=10 ** rng.uniform(-2.0, 0.5),
        interleave_threshold=0.0,
        capacity_gate=1.0 if rng.random() < 0.8 else 0.0,
    )


def _seed_weights() -> list[Weights]:
    """Structured anchors make a short run useful before random exploration."""
    anchors: list[Weights] = []
    for aid in (-2.0, -0.5, 0.0, 0.5, 2.0):
        for depth in (-2.0, 0.0, 2.0):
            for dirty in (-2.0, 0.0, 2.0):
                anchors.append(
                    Weights(
                        alloc_wait=12.0,
                        alloc_pressure=1.0,
                        alloc_dirty=dirty,
                        alloc_users=-0.25,
                        alloc_id=aid,
                        alloc_depth=depth,
                        op_release_dirty=5.0,
                        op_release_clean=1.0,
                        op_touched=0.2,
                        op_unlock_free=3.0,
                        op_unlock_op=0.5,
                        capacity_gate=1.0,
                    )
                )
    return anchors


def spill_aware_order(instance, weights: Weights, seed: int) -> list[int]:
    nodes = {node.id: node for node in instance.nodes}
    n_nodes = max(1, len(nodes))
    successors: dict[int, list[int]] = defaultdict(list)
    predecessors: dict[int, list[int]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in nodes}
    for edge in instance.edges:
        successors[edge.src].append(edge.dst)
        predecessors[edge.dst].append(edge.src)
        indegree[edge.dst] += 1

    alloc_by_buf = {
        node.buf_id: node
        for node in instance.nodes
        if node.op == "ALLOC" and node.buf_id is not None
    }
    clean = {buf for node in instance.nodes if node.op == "COPY_IN" for buf in node.bufs}
    remaining_users: dict[int, int] = defaultdict(int)
    for node in instance.nodes:
        if node.op not in {"ALLOC", "FREE"}:
            for buf_id in node.bufs:
                remaining_users[buf_id] += 1
    initial_users = dict(remaining_users)

    # Static distance to a FREE (or another terminal) is a generic locality
    # feature: it does not inspect op motifs or case names.
    min_terminal_depth: dict[int, int] = {}
    for node_id in reversed(_plain_topological(nodes, successors, indegree)):
        if not successors[node_id]:
            min_terminal_depth[node_id] = 0
        else:
            min_terminal_depth[node_id] = 1 + min(
                min_terminal_depth[dst] for dst in successors[node_id]
            )
    max_depth = max(min_terminal_depth.values(), default=1)

    rng = random.Random(seed)
    noise = {node_id: rng.uniform(-1.0, 1.0) for node_id in nodes}
    ready_free: set[int] = set()
    ready_ops: set[int] = set()
    ready_alloc: set[int] = set()
    alloc_heap: list[tuple[float, int]] = []
    current = defaultdict(int)
    order: list[int] = []

    def successor_wait(node_id: int) -> int:
        return min(
            (indegree[dst] for dst in successors[node_id] if nodes[dst].op != "FREE"),
            default=n_nodes,
        )

    def alloc_score(node_id: int) -> float:
        node = nodes[node_id]
        cap = CACHE_CAPACITIES.get(node.mem_type or "", max(1, node.size))
        pressure = node.size / cap
        is_dirty = 0.0 if node.buf_id in clean else 1.0
        users = initial_users.get(node.buf_id, 0) / 8.0
        depth = min_terminal_depth[node_id] / max_depth
        return (
            weights.alloc_wait * successor_wait(node_id)
            + weights.alloc_pressure * pressure
            + weights.alloc_dirty * is_dirty
            + weights.alloc_users * users
            + weights.alloc_id * (node_id / n_nodes)
            + weights.alloc_depth * depth
            + weights.alloc_noise * noise[node_id]
        )

    def push_alloc(node_id: int) -> None:
        heapq.heappush(alloc_heap, (alloc_score(node_id), node_id))

    def add_ready(node_id: int) -> None:
        op = nodes[node_id].op
        if op == "FREE":
            ready_free.add(node_id)
        elif op == "ALLOC":
            ready_alloc.add(node_id)
            push_alloc(node_id)
        else:
            ready_ops.add(node_id)

    def take_alloc() -> int:
        skipped: list[tuple[float, int]] = []
        while alloc_heap:
            old_score, node_id = heapq.heappop(alloc_heap)
            if node_id not in ready_alloc:
                continue
            score = alloc_score(node_id)
            if not math.isclose(old_score, score, rel_tol=0.0, abs_tol=1e-12):
                heapq.heappush(alloc_heap, (score, node_id))
                continue
            node = nodes[node_id]
            cap = CACHE_CAPACITIES.get(node.mem_type or "", 1 << 60)
            if (
                weights.capacity_gate > 0
                and current[node.mem_type or ""] + node.size > cap * weights.capacity_gate
            ):
                skipped.append((score, node_id))
                continue
            ready_alloc.remove(node_id)
            for item in skipped:
                heapq.heappush(alloc_heap, item)
            return node_id
        if skipped:
            # Every ready allocation exceeds its cache.  Force the best one to
            # make forward progress, as a real spilling scheduler must.
            score, node_id = min(skipped)
            ready_alloc.remove(node_id)
            for item in skipped:
                if item[1] != node_id:
                    heapq.heappush(alloc_heap, item)
            return node_id
        raise RuntimeError("ALLOC heap exhausted")

    def normalized_bytes(buf_id: int, dirty_factor: bool) -> float:
        alloc = alloc_by_buf.get(buf_id)
        if alloc is None:
            return 0.0
        cap = CACHE_CAPACITIES.get(alloc.mem_type or "", max(1, alloc.size))
        factor = 2.0 if dirty_factor and buf_id not in clean else 1.0
        return factor * alloc.size / cap

    def op_utility(node_id: int) -> float:
        node = nodes[node_id]
        rel_dirty = sum(
            normalized_bytes(buf_id, True)
            for buf_id in node.bufs
            if remaining_users.get(buf_id, 0) == 1
        )
        rel_clean = sum(
            normalized_bytes(buf_id, False)
            for buf_id in node.bufs
            if remaining_users.get(buf_id, 0) == 1 and buf_id in clean
        )
        touched = sum(normalized_bytes(buf_id, False) for buf_id in node.bufs)
        unlock_free = sum(
            1 for dst in successors[node_id] if indegree[dst] == 1 and nodes[dst].op == "FREE"
        )
        unlock_op = sum(
            1
            for dst in successors[node_id]
            if indegree[dst] == 1 and nodes[dst].op not in {"ALLOC", "FREE"}
        )
        return (
            weights.op_release_dirty * rel_dirty
            + weights.op_release_clean * rel_clean
            + weights.op_touched * touched
            + weights.op_unlock_free * unlock_free
            + weights.op_unlock_op * unlock_op
            + weights.op_id * (node_id / n_nodes)
            + weights.op_noise * noise[node_id]
        )

    for node_id, degree in indegree.items():
        if degree == 0:
            add_ready(node_id)

    while ready_free or ready_ops or ready_alloc:
        if ready_free:
            # Largest normalized release first; this only affects simultaneous
            # sink nodes and is deterministic.
            node_id = max(
                ready_free,
                key=lambda x: (
                    normalized_bytes(nodes[x].buf_id, True),
                    -x,
                ),
            )
            ready_free.remove(node_id)
        elif ready_ops:
            node_id = max(ready_ops, key=lambda x: (op_utility(x), -x))
            ready_ops.remove(node_id)
        else:
            node_id = take_alloc()

        node = nodes[node_id]
        order.append(node_id)
        if node.op == "ALLOC" and node.mem_type is not None:
            current[node.mem_type] += node.size
        elif node.op == "FREE" and node.mem_type is not None:
            current[node.mem_type] -= node.size
        elif node.op not in {"ALLOC", "FREE"}:
            for buf_id in node.bufs:
                if remaining_users[buf_id] > 0:
                    remaining_users[buf_id] -= 1

        for dst in successors[node_id]:
            indegree[dst] -= 1
            # Scores of ready allocation predecessors change when a successor's
            # remaining predecessor count changes.
            for pred in predecessors[dst]:
                if pred in ready_alloc:
                    push_alloc(pred)
            if indegree[dst] == 0:
                add_ready(dst)

    if len(order) != len(nodes):
        raise ValueError("Input graph is not a DAG")
    return order


def _plain_topological(nodes, successors, original_indegree) -> list[int]:
    indegree = dict(original_indegree)
    heap = [node_id for node_id, degree in indegree.items() if degree == 0]
    heapq.heapify(heap)
    order: list[int] = []
    while heap:
        node_id = heapq.heappop(heap)
        order.append(node_id)
        for dst in successors[node_id]:
            indegree[dst] -= 1
            if indegree[dst] == 0:
                heapq.heappush(heap, dst)
    return order


def concrete_score(instance, base_order, policies=("dist_size_cost",)):
    best = None
    for policy in policies:
        try:
            order, memory, spills = core_solver._assign_memory_with_spills(
                instance,
                base_order,
                prefetch_window=0,
                victim_policy=policy,
            )
        except RuntimeError:
            continue
        result = evaluate(instance, order, memory, spills)
        if not result.valid:
            continue
        key = (result.metrics["extra"], len(spills), result.metrics["time"])
        if best is None or key < best[0]:
            best = (key, order, memory, spills, policy, result)
    if best is None:
        raise RuntimeError("No valid concrete assignment")
    return best


def relocation_search(
    instance,
    start_order: list[int],
    iterations: int,
    seed: int,
    report_every_improvement: bool = True,
):
    """Concrete-cost simulated annealing over valid single-node relocations.

    This move operator is completely graph-generic: a sampled node can move to
    any point between its latest predecessor and earliest successor.  Each
    proposal is rescored by the real assignment routine, not a live-set proxy.
    """
    rng = random.Random(seed)
    pred: dict[int, list[int]] = defaultdict(list)
    succ: dict[int, list[int]] = defaultdict(list)
    for edge in instance.edges:
        pred[edge.dst].append(edge.src)
        succ[edge.src].append(edge.dst)

    def raw_score(base_order):
        try:
            full_order, memory, spills = core_solver._assign_memory_with_spills(
                instance, base_order, prefetch_window=0, victim_policy="dist_size_cost"
            )
        except RuntimeError:
            return None
        nodes = {node.id: node for node in instance.nodes}
        extra = core_solver._extra_traffic(spills, nodes)
        return (extra, len(spills)), full_order, memory, spills

    current_order = list(start_order)
    current = raw_score(current_order)
    if current is None:
        raise RuntimeError("Local-search seed cannot be assigned")
    best_order = list(current_order)
    best = current
    n = len(current_order)
    start = time.perf_counter()

    # Bias samples toward ALLOC/operations. FREE nodes are already scheduled
    # eagerly by most seeds and moving them later almost never helps P2.
    sample_nodes = [
        node.id
        for node in instance.nodes
        for _ in range(3 if node.op == "ALLOC" else 2 if node.op != "FREE" else 1)
    ]

    for iteration in range(iterations):
        position = {node_id: pos for pos, node_id in enumerate(current_order)}
        node_id = rng.choice(sample_nodes)
        old_pos = position[node_id]
        lo = max((position[x] + 1 for x in pred[node_id]), default=0)
        hi = min((position[x] for x in succ[node_id]), default=n)
        if hi - lo <= 1:
            continue
        target = rng.randrange(lo, hi)
        proposal_order = list(current_order)
        proposal_order.pop(old_pos)
        if target > old_pos:
            target -= 1
        if target == old_pos:
            continue
        proposal_order.insert(target, node_id)

        # The interval calculation above is deliberately followed by an exact
        # incident-edge check to avoid subtle insertion off-by-one errors.
        ppos = {x: pos for pos, x in enumerate(proposal_order)}
        if any(ppos[x] >= ppos[node_id] for x in pred[node_id]):
            continue
        if any(ppos[node_id] >= ppos[x] for x in succ[node_id]):
            continue
        proposal = raw_score(proposal_order)
        if proposal is None:
            continue

        delta = proposal[0][0] - current[0][0]
        # Start with a modest temperature (roughly one medium buffer spill) and
        # cool to greedy hill climbing.
        fraction = iteration / max(1, iterations - 1)
        temperature = 512.0 * (1.0 - fraction) + 1.0
        if delta < 0 or (delta == 0 and proposal[0][1] <= current[0][1]) or rng.random() < math.exp(
            -delta / temperature
        ):
            current_order = proposal_order
            current = proposal
            if current[0] < best[0]:
                best_order = list(current_order)
                best = current
                if report_every_improvement:
                    print(
                        f"local iter={iteration} extra={best[0][0]} spills={best[0][1]} "
                        f"elapsed={time.perf_counter() - start:.1f}s",
                        flush=True,
                    )

    return best_order, best


def globally_optimal_evictions(instance, base_order: list[int], time_limit: float = 60.0):
    """Optimize all keep/spill gaps for a fixed topological order.

    A buffer has a sequence of mandatory events (ALLOC, every user, FREE).
    Keeping it resident across a gap avoids exactly one evaluator spill charge.
    Optional intervals plus a cumulative constraint therefore express the
    fixed-order, fully-associative minimum-extra problem exactly.  Deterministic
    greedy trials, followed by NoOverlap2D when needed, assign concrete offsets
    to selected residency segments before canonical spill nodes are emitted.
    """
    position = {node_id: pos for pos, node_id in enumerate(base_order)}
    alloc = {
        node.buf_id: node
        for node in instance.nodes
        if node.op == "ALLOC" and node.buf_id is not None
    }
    clean = {buf for node in instance.nodes if node.op == "COPY_IN" for buf in node.bufs}
    events: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for node in instance.nodes:
        if node.op == "ALLOC" and node.buf_id is not None:
            events[node.buf_id].append((position[node.id], node.id))
        elif node.op == "FREE" and node.buf_id is not None:
            events[node.buf_id].append((position[node.id], node.id))
        elif node.op not in {"ALLOC", "FREE"}:
            for buf_id in set(node.bufs):
                if buf_id in alloc:
                    events[buf_id].append((position[node.id], node.id))
    for buf_id in events:
        events[buf_id] = sorted(set(events[buf_id]))

    model = cp_model.CpModel()
    keep_vars: dict[tuple[int, int], cp_model.IntVar] = {}
    total_gap_cost = 0
    objective_terms = []
    for cache, capacity in CACHE_CAPACITIES.items():
        intervals = []
        demands = []
        for buf_id, buf_events in events.items():
            alloc_node = alloc[buf_id]
            if alloc_node.mem_type != cache:
                continue
            # Mandatory one-tick event slots ensure that all operands of an op
            # are simultaneously resident even when both neighboring gaps spill.
            for event_index, (pos, _node_id) in enumerate(buf_events):
                intervals.append(
                    model.new_fixed_size_interval_var(
                        2 * pos, 1, f"event_{cache}_{buf_id}_{event_index}"
                    )
                )
                demands.append(alloc_node.size)
            gap_cost = alloc_node.size * (1 if buf_id in clean else 2)
            for gap_index, ((left, _), (right, _)) in enumerate(
                zip(buf_events, buf_events[1:])
            ):
                keep = model.new_bool_var(f"keep_{cache}_{buf_id}_{gap_index}")
                keep_vars[(buf_id, gap_index)] = keep
                interval = model.new_optional_fixed_size_interval_var(
                    2 * left + 1,
                    2 * (right - left) - 1,
                    keep,
                    f"gap_{cache}_{buf_id}_{gap_index}",
                )
                intervals.append(interval)
                demands.append(alloc_node.size)
                objective_terms.append(gap_cost * keep)
                total_gap_cost += gap_cost
        model.add_cumulative(intervals, demands, capacity)
    model.maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    status = solver.solve(model)
    if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
        raise RuntimeError(f"Eviction model failed: {solver.status_name(status)}")

    kept = {
        key: bool(solver.value(var))
        for key, var in keep_vars.items()
    }
    lower_bound_extra = total_gap_cost - round(solver.best_objective_bound)
    selected_extra = total_gap_cost - round(solver.objective_value)

    # Materialize maximal resident runs.  Fixed x intervals represent time;
    # variable y intervals represent byte offsets.  NoOverlap2D is the exact
    # dynamic-storage-allocation check missing from a pure live-byte bound.
    segments: list[dict] = []
    for buf_id, buf_events in events.items():
        run_start = 0
        for gap_index in range(len(buf_events) - 1):
            if not kept[(buf_id, gap_index)]:
                segments.append(
                    {
                        "buf_id": buf_id,
                        "first_event": run_start,
                        "last_event": gap_index,
                        "start": 2 * buf_events[run_start][0],
                        "end": 2 * buf_events[gap_index][0] + 1,
                    }
                )
                run_start = gap_index + 1
        segments.append(
            {
                "buf_id": buf_id,
                "first_event": run_start,
                "last_event": len(buf_events) - 1,
                "start": 2 * buf_events[run_start][0],
                "end": 2 * buf_events[-1][0] + 1,
            }
        )

    def greedy_pack(trial_seed: int) -> bool:
        """Fast left-edge/best-fit attempts before the exact 2-D packer."""
        rng = random.Random(trial_seed)
        assigned: dict[int, int] = {}
        for cache, capacity in CACHE_CAPACITIES.items():
            cache_indices = [
                index
                for index, segment in enumerate(segments)
                if alloc[segment["buf_id"]].mem_type == cache
            ]
            by_start: dict[int, list[int]] = defaultdict(list)
            for index in cache_indices:
                by_start[segments[index]["start"]].append(index)
            active: list[int] = []
            for start in sorted(by_start):
                active = [index for index in active if segments[index]["end"] > start]
                occupied = sorted(
                    (
                        assigned[index],
                        assigned[index] + alloc[segments[index]["buf_id"]].size,
                    )
                    for index in active
                )
                free_ranges = []
                cursor = 0
                for left, right in occupied:
                    if cursor < left:
                        free_ranges.append((cursor, left - cursor))
                    cursor = max(cursor, right)
                if cursor < capacity:
                    free_ranges.append((cursor, capacity - cursor))

                group = by_start[start]
                # Vary simultaneous-start ordering across trials.
                if trial_seed % 4 == 0:
                    group.sort(key=lambda i: -alloc[segments[i]["buf_id"]].size)
                elif trial_seed % 4 == 1:
                    group.sort(key=lambda i: alloc[segments[i]["buf_id"]].size)
                elif trial_seed % 4 == 2:
                    group.sort(key=lambda i: -segments[i]["end"])
                else:
                    rng.shuffle(group)
                for index in group:
                    size = alloc[segments[index]["buf_id"]].size
                    fits = [
                        (slot, item)
                        for slot, item in enumerate(free_ranges)
                        if item[1] >= size
                    ]
                    if not fits:
                        return False
                    mode = (trial_seed // 4) % 3
                    if mode == 0:
                        slot, (left, length) = min(fits, key=lambda pair: pair[1][0])
                        offset = left
                    elif mode == 1:
                        slot, (left, length) = min(fits, key=lambda pair: pair[1][1] - size)
                        offset = left
                    else:
                        slot, (left, length) = max(fits, key=lambda pair: pair[1][0])
                        offset = left + length - size
                    free_ranges.pop(slot)
                    if offset > left:
                        free_ranges.append((left, offset - left))
                    if offset + size < left + length:
                        free_ranges.append((offset + size, left + length - offset - size))
                    free_ranges.sort()
                    assigned[index] = offset
                    active.append(index)
        for index, offset in assigned.items():
            segments[index]["offset"] = offset
        return True

    packed_greedily = any(greedy_pack(seed) for seed in range(48))
    if packed_greedily:
        packing_status = "GREEDY_VALID"
    else:
        pack = cp_model.CpModel()
        segment_offsets = []
        for cache, capacity in CACHE_CAPACITIES.items():
            x_intervals = []
            y_intervals = []
            for segment_index, segment in enumerate(segments):
                alloc_node = alloc[segment["buf_id"]]
                if alloc_node.mem_type != cache:
                    continue
                size = alloc_node.size
                offset = pack.new_int_var(0, capacity - size, f"offset_{segment_index}")
                x_interval = pack.new_fixed_size_interval_var(
                    segment["start"],
                    segment["end"] - segment["start"],
                    f"life_{segment_index}",
                )
                y_interval = pack.new_fixed_size_interval_var(
                    offset, size, f"space_{segment_index}"
                )
                segment_offsets.append((segment_index, offset))
                x_intervals.append(x_interval)
                y_intervals.append(y_interval)
            pack.add_no_overlap_2d(x_intervals, y_intervals)

        pack_solver = cp_model.CpSolver()
        pack_solver.parameters.max_time_in_seconds = time_limit
        pack_solver.parameters.num_search_workers = 8
        pack_status = pack_solver.solve(pack)
        if pack_status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
            raise RuntimeError(
                "Optimal fully-associative eviction set has no concrete contiguous layout: "
                f"{pack_solver.status_name(pack_status)}"
            )
        for segment_index, offset in segment_offsets:
            segments[segment_index]["offset"] = pack_solver.value(offset)
        packing_status = pack_solver.status_name(pack_status)

    segments_by_buf: dict[int, list[dict]] = defaultdict(list)
    for segment in segments:
        segments_by_buf[segment["buf_id"]].append(segment)
    for buf_segments in segments_by_buf.values():
        buf_segments.sort(key=lambda item: item["first_event"])

    memory = {buf_id: buf_segments[0]["offset"] for buf_id, buf_segments in segments_by_buf.items()}
    spill_entries: list[tuple[int, int]] = []
    outs_after: dict[int, list[int]] = defaultdict(list)
    ins_before: dict[int, list[int]] = defaultdict(list)
    for buf_id, buf_segments in segments_by_buf.items():
        buf_events = events[buf_id]
        for previous, following in zip(buf_segments, buf_segments[1:]):
            left_event = buf_events[previous["last_event"]][1]
            right_event = buf_events[following["first_event"]][1]
            spill_index = len(spill_entries)
            spill_entries.append((buf_id, following["offset"]))
            outs_after[left_event].append(spill_index)
            ins_before[right_event].append(spill_index)

    num_original = len(instance.nodes)
    order: list[int] = []
    for node_id in base_order:
        order.extend(num_original + 2 * index + 1 for index in ins_before[node_id])
        order.append(node_id)
        order.extend(num_original + 2 * index for index in outs_after[node_id])

    result = evaluate(instance, order, memory, spill_entries)
    if not result.valid:
        raise RuntimeError(f"Constructed optimal schedule is invalid: {result.errors[:3]}")
    if result.metrics["extra"] != selected_extra:
        raise AssertionError((result.metrics["extra"], selected_extra))
    return {
        "order": order,
        "memory": memory,
        "spills": spill_entries,
        "result": result,
        "solver_status": solver.status_name(status),
        "selected_extra": selected_extra,
        "lower_bound_extra": lower_bound_extra,
        "optimality_gap": selected_extra - lower_bound_extra,
        "packing_status": packing_status,
    }


def run_case(case: str, trials: int, master_seed: int, out_dir: Path) -> dict:
    instance = load_json(ROOT / "data" / "raw" / "json" / f"{case}.json", problem_id=2)
    candidates = _seed_weights()
    rng = random.Random(master_seed)
    while len(candidates) < trials:
        candidates.append(_random_weights(rng))
    candidates = candidates[:trials]

    best = None
    start = time.perf_counter()
    history = []
    for index, weights in enumerate(candidates):
        seed = master_seed * 1_000_003 + index
        base_order = spill_aware_order(instance, weights, seed)
        try:
            scored = concrete_score(instance, base_order)
        except RuntimeError:
            continue
        key, order, memory, spills, policy, result = scored
        row = {
            "trial": index,
            "seed": seed,
            "weights": asdict(weights),
            "extra": key[0],
            "spills": key[1],
            "time": key[2],
            "policy": policy,
            "valid": result.valid,
        }
        history.append(row)
        if best is None or key < best[0]:
            best = (key, row, base_order, order, memory, spills)
            print(
                f"{case}: trial={index} extra={key[0]} spills={key[1]} "
                f"time={key[2]} elapsed={time.perf_counter() - start:.1f}s",
                flush=True,
            )

    assert best is not None
    key, best_row, base_order, order, memory, spills = best
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "case": case,
        "trials": trials,
        "wall_seconds": time.perf_counter() - start,
        "best": best_row,
        "history": history,
    }
    (out_dir / f"{case}_search.json").write_text(json.dumps(summary, indent=2))
    (out_dir / f"{case}_base_order.txt").write_text("".join(f"{x}\n" for x in base_order))
    (out_dir / f"P2_{case}_schedule.txt").write_text("".join(f"{x}\n" for x in order))
    (out_dir / f"P2_{case}_memory.txt").write_text(
        "".join(f"{buf}:{memory[buf]}\n" for buf in sorted(memory))
    )
    (out_dir / f"P2_{case}_spill.txt").write_text(
        "".join(f"{buf}:{offset}\n" for buf, offset in spills)
    )
    return summary


def run_exact_case(case: str, order_name: str, time_limit: float, out_dir: Path) -> dict:
    instance = load_json(ROOT / "data" / "raw" / "json" / f"{case}.json", problem_id=2)
    if order_name == "unlock_frontier":
        base_order = core_solver._unlock_frontier_order(instance)
    elif order_name == "id_raw":
        base_order = core_solver._id_raw_order(instance)
    elif order_name in {"capfit_id", "capfit", "p1"}:
        base_order = core_solver._memory_aware_order(instance, variant=order_name)
    else:
        raise ValueError(order_name)
    started = time.perf_counter()
    exact = globally_optimal_evictions(instance, base_order, time_limit=time_limit)
    elapsed = time.perf_counter() - started
    result = exact["result"]
    summary = {
        "case": case,
        "problem": 2,
        "base_order": order_name,
        "wall_seconds": elapsed,
        "solver_status": exact["solver_status"],
        "packing_status": exact["packing_status"],
        "lower_bound_extra": exact["lower_bound_extra"],
        "optimality_gap": exact["optimality_gap"],
        "valid": result.valid,
        **result.metrics,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"P2_{case}_{order_name}_exact"
    (out_dir / f"{stem}.json").write_text(json.dumps(summary, indent=2))
    (out_dir / f"{stem}_schedule.txt").write_text(
        "".join(f"{node_id}\n" for node_id in exact["order"])
    )
    (out_dir / f"{stem}_memory.txt").write_text(
        "".join(f"{buf_id}:{exact['memory'][buf_id]}\n" for buf_id in sorted(exact["memory"]))
    )
    (out_dir / f"{stem}_spill.txt").write_text(
        "".join(f"{buf_id}:{offset}\n" for buf_id, offset in exact["spills"])
    )
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="+", default=["Conv_Case0", "FlashAttention_Case0"])
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260711)
    parser.add_argument(
        "--exact-order",
        choices=["unlock_frontier", "id_raw", "capfit_id", "capfit", "p1"],
        help="Skip weight search and globally optimize evictions for this fixed order.",
    )
    parser.add_argument("--time-limit", type=float, default=120.0)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "autoresearch_v2" / "agent_direct",
    )
    args = parser.parse_args()
    cases = CASES if args.cases == ["all"] else args.cases
    if args.exact_order:
        summaries = [
            run_exact_case(case, args.exact_order, args.time_limit, args.out)
            for case in cases
        ]
        (args.out / f"exact_{args.exact_order}_summary.json").write_text(
            json.dumps(summaries, indent=2)
        )
        return
    summaries = [run_case(case, args.trials, args.seed, args.out) for case in cases]
    compact = [
        {
            "case": item["case"],
            "trials": item["trials"],
            "wall_seconds": item["wall_seconds"],
            "best": item["best"],
        }
        for item in summaries
    ]
    (args.out / "summary.json").write_text(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()
