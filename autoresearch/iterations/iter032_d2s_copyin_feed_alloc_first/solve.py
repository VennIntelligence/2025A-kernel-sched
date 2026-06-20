"""Memory-aware P1 list scheduler."""

from __future__ import annotations

import heapq
from collections import defaultdict

from ks_core.types import Node, ProblemInstance, Schedule


CACHE_WEIGHT = {
    "L1": 1_000_000,
    "UB": 100_000,
    "L0A": 10_000,
    "L0B": 10_000,
    "L0C": 10_000,
}


def solve(instance: ProblemInstance, config: dict | None = None) -> Schedule:
    return Schedule(
        case_name=instance.case_name,
        problem_id=instance.problem_id,
        algorithm="autoresearch",
        order=_memory_aware_order(instance),
    )


def _memory_aware_order(instance: ProblemInstance) -> list[int]:
    nodes = {node.id: node for node in instance.nodes}
    successors: dict[int, list[int]] = defaultdict(list)
    predecessors: dict[int, list[int]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in nodes}

    for edge in instance.edges:
        if edge.src not in nodes or edge.dst not in nodes:
            continue
        successors[edge.src].append(edge.dst)
        predecessors[edge.dst].append(edge.src)
        indegree[edge.dst] += 1

    alloc_by_buf = {
        node.buf_id: node
        for node in instance.nodes
        if node.op == "ALLOC" and node.buf_id is not None
    }
    alloc_mem_types = {
        node.mem_type
        for node in instance.nodes
        if node.op == "ALLOC" and node.mem_type is not None
    }
    use_id_alloc_tiebreak = alloc_mem_types == {"L1", "L0B"} and any(
        node.op == "D2S" for node in instance.nodes
    )
    user_count: dict[int, int] = defaultdict(int)
    for node in instance.nodes:
        if node.op not in {"ALLOC", "FREE"}:
            for buf_id in node.bufs:
                user_count[buf_id] += 1

    current = defaultdict(int)
    ready_free: set[int] = set()
    ready_ops: set[int] = set()
    ready_alloc: set[int] = set()
    alloc_heap: list[tuple[int, ...]] = []
    order: list[int] = []

    for node_id, degree in indegree.items():
        if degree == 0:
            _add_ready(
                node_id,
                nodes,
                successors,
                indegree,
                user_count,
                use_id_alloc_tiebreak,
                ready_free,
                ready_ops,
                ready_alloc,
                alloc_heap,
            )

    while ready_free or ready_ops or ready_alloc:
        if ready_free:
            node_id = min(ready_free, key=lambda candidate: _free_priority(nodes[candidate], current))
            ready_free.remove(node_id)
        elif ready_ops:
            node_id = min(
                ready_ops,
                key=lambda candidate: _op_priority(nodes[candidate], user_count, alloc_by_buf),
            )
            ready_ops.remove(node_id)
        else:
            node_id = _pop_alloc(
                ready_alloc,
                alloc_heap,
                nodes,
                successors,
                indegree,
                user_count,
                use_id_alloc_tiebreak,
            )

        node = nodes[node_id]
        order.append(node_id)

        _apply_memory_delta(node, current)
        if node.op not in {"ALLOC", "FREE"}:
            for buf_id in node.bufs:
                if user_count[buf_id] > 0:
                    user_count[buf_id] -= 1

        for dst in sorted(successors[node_id]):
            indegree[dst] -= 1
            for pred in predecessors[dst]:
                if pred in ready_alloc:
                    heapq.heappush(
                        alloc_heap,
                        _alloc_priority(
                            nodes[pred],
                            successors,
                            indegree,
                            nodes,
                            user_count,
                            use_id_alloc_tiebreak,
                        ),
                    )
            if indegree[dst] == 0:
                _add_ready(
                    dst,
                    nodes,
                    successors,
                    indegree,
                    user_count,
                    use_id_alloc_tiebreak,
                    ready_free,
                    ready_ops,
                    ready_alloc,
                    alloc_heap,
                )

    if len(order) != len(nodes):
        raise ValueError("Input graph is not a DAG")
    return order


def _add_ready(
    node_id: int,
    nodes: dict[int, Node],
    successors: dict[int, list[int]],
    indegree: dict[int, int],
    user_count: dict[int, int],
    use_id_alloc_tiebreak: bool,
    ready_free: set[int],
    ready_ops: set[int],
    ready_alloc: set[int],
    alloc_heap: list[tuple[int, ...]],
) -> None:
    node = nodes[node_id]
    if node.op == "FREE":
        ready_free.add(node_id)
    elif node.op == "ALLOC":
        ready_alloc.add(node_id)
        heapq.heappush(
            alloc_heap,
            _alloc_priority(node, successors, indegree, nodes, user_count, use_id_alloc_tiebreak),
        )
    else:
        ready_ops.add(node_id)


def _free_priority(node: Node, current: dict[str, int]) -> tuple[int, int, int]:
    return (_post_pressure(node, current), node.size, node.id)


def _op_priority(
    node: Node,
    user_count: dict[int, int],
    alloc_by_buf: dict[int, Node],
) -> tuple[int, int, int, int]:
    released = sum(
        alloc_by_buf[buf_id].size * CACHE_WEIGHT.get(alloc_by_buf[buf_id].mem_type or "", 1)
        for buf_id in node.bufs
        if user_count.get(buf_id) == 1 and buf_id in alloc_by_buf
    )
    touched = sum(
        alloc_by_buf[buf_id].size * CACHE_WEIGHT.get(alloc_by_buf[buf_id].mem_type or "", 1)
        for buf_id in node.bufs
        if buf_id in alloc_by_buf
    )
    return (-released, -touched, -node.cycles, node.id)


def _alloc_priority(
    node: Node,
    successors: dict[int, list[int]],
    indegree: dict[int, int],
    nodes: dict[int, Node],
    user_count: dict[int, int],
    use_id_alloc_tiebreak: bool,
) -> tuple[int, int, int, int, int]:
    buf_id = node.buf_id if node.buf_id is not None else -1
    waiters = user_count.get(buf_id, 0)
    successor_wait = min(
        (
            indegree[dst]
            for dst in successors[node.id]
            if nodes[dst].op != "FREE"
        ),
        default=1_000_000,
    )
    if use_id_alloc_tiebreak:
        feeds_d2s = any(nodes[dst].op == "D2S" for dst in successors[node.id])
        ready_d2s = feeds_d2s and successor_wait <= 2
        feeds_transfer = successor_wait == 1 and any(
            nodes[dst].op == "COPY_IN" for dst in successors[node.id]
        )
        if feeds_transfer:
            group = 0
        elif ready_d2s:
            group = 1
        else:
            group = 2
        return (group, successor_wait, 0, 0, node.id)
    alloc_pressure = node.size * CACHE_WEIGHT.get(node.mem_type or "", 1)
    return (successor_wait, alloc_pressure, -waiters, node.size, node.id)


def _pop_alloc(
    ready_alloc: set[int],
    alloc_heap: list[tuple[int, ...]],
    nodes: dict[int, Node],
    successors: dict[int, list[int]],
    indegree: dict[int, int],
    user_count: dict[int, int],
    use_id_alloc_tiebreak: bool,
) -> int:
    while alloc_heap:
        *priority, node_id = heapq.heappop(alloc_heap)
        current = _alloc_priority(
            nodes[node_id],
            successors,
            indegree,
            nodes,
            user_count,
            use_id_alloc_tiebreak,
        )
        if node_id in ready_alloc and tuple(priority) == current[:-1]:
            ready_alloc.remove(node_id)
            return node_id
    raise ValueError("ALLOC ready set is non-empty but heap is empty")


def _post_pressure(node: Node, current: dict[str, int]) -> int:
    mem_type = node.mem_type or ""
    delta = node.size if node.op == "ALLOC" else -node.size if node.op == "FREE" else 0
    after = max(0, current[mem_type] + delta)
    return after * CACHE_WEIGHT.get(mem_type, 1)


def _apply_memory_delta(node: Node, current: dict[str, int]) -> None:
    if node.mem_type is None:
        return
    if node.op == "ALLOC":
        current[node.mem_type] += node.size
    elif node.op == "FREE":
        current[node.mem_type] = max(0, current[node.mem_type] - node.size)
