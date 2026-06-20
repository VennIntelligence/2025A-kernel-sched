"""Unified P1/P2/P3 solver.

P1 keeps the promoted iter031 memory-aware list scheduler (lexicographic score).

P2/P3 take a global view instead of P1's max_L1-only objective:

1. Generate candidate topological orders (id-tiebreak gated, generic, and a
   capacity-normalized variant that values UB/L0 overflow as much as L1).
2. Pick the candidate with the smallest predicted spill traffic, i.e. the
   capacity overflow integral over the schedule, not the lexicographic P1 key.
3. Assign physical offsets with best-fit and insert SPILL_OUT/SPILL_IN pairs
   with farthest-next-use (Belady) victim selection when a cache overflows.
"""

from __future__ import annotations

import heapq
from collections import defaultdict

from ks_core.evaluator import compute_total_time
from ks_core.types import Node, ProblemInstance, Schedule

CACHE_CAPACITIES = {"L1": 4096, "UB": 1024, "L0A": 256, "L0B": 256, "L0C": 512}

# Lexicographic weights used by the promoted P1 scheduler (iter031).
P1_CACHE_WEIGHT = {
    "L1": 1_000_000,
    "UB": 100_000,
    "L0A": 10_000,
    "L0B": 10_000,
    "L0C": 10_000,
}

# Capacity-normalized weights: one unit of UB/L0 is far scarcer than L1.
NORM_CACHE_WEIGHT = {
    cache: 1_000_000 // capacity for cache, capacity in CACHE_CAPACITIES.items()
}


def solve(instance: ProblemInstance, config: dict | None = None) -> Schedule:
    schedule = Schedule(
        case_name=instance.case_name,
        problem_id=instance.problem_id,
        algorithm="autoresearch",
    )
    if instance.problem_id == 1:
        schedule.order = _memory_aware_order(instance, variant="p1")
        return schedule

    nodes = {node.id: node for node in instance.nodes}
    # P2 minimizes extra, which a prefetch window can only increase, so a tight
    # window grid suffices. P3 minimizes time, where reload-hiding prefetch is
    # the main lever, so explore a wider window grid for it.
    windows = (0, 5, 40, 80, 120) if instance.problem_id >= 3 else (0, 5, 40)
    best = None
    for base_order in _candidate_orders(instance):
        for window in windows:
            order, memory, spill_entries = _assign_memory_with_spills(
                instance, base_order, prefetch_window=window
            )
            extra = _extra_traffic(spill_entries, nodes)
            time = compute_total_time(
                order,
                nodes,
                instance.edges,
                memory=memory,
                spill_entries=spill_entries,
                num_original_nodes=len(instance.nodes),
            )
            if instance.problem_id >= 3:
                key = (time, extra, len(spill_entries))
            else:
                key = (extra, len(spill_entries), time)
            if best is None or key < best[0]:
                best = (key, order, memory, spill_entries)
    _, schedule.order, schedule.memory, schedule.spill_entries = best
    return schedule


def _extra_traffic(spill_entries: list[tuple[int, int]], nodes: dict[int, Node]) -> int:
    alloc_size = {n.buf_id: n.size for n in nodes.values() if n.op == "ALLOC"}
    copy_in = {b for n in nodes.values() if n.op == "COPY_IN" for b in n.bufs}
    return sum(
        alloc_size[b] if b in copy_in else 2 * alloc_size[b] for b, _ in spill_entries
    )


# ---------------------------------------------------------------------------
# Candidate order selection for P2/P3
# ---------------------------------------------------------------------------

def _candidate_orders(instance: ProblemInstance) -> list[list[int]]:
    return [
        _memory_aware_order(instance, variant="capfit_id"),
        _memory_aware_order(instance, variant="p1"),
        _id_raw_order(instance),
    ]


def _id_raw_order(instance: ProblemInstance) -> list[int]:
    """Pure node-id list order with FREE > op > ALLOC tie-break, no capacity
    throttle. The native id order keeps a buffer's COPY_IN inputs resident
    through its compute window, which lets the spill engine evict cheap
    COPY_IN buffers at half price during overflow (helps Conv1/FA0 P2 extra).
    """
    nodes = {node.id: node for node in instance.nodes}
    successors: dict[int, list[int]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in nodes}
    for edge in instance.edges:
        if edge.src not in nodes or edge.dst not in nodes:
            continue
        successors[edge.src].append(edge.dst)
        indegree[edge.dst] += 1

    ready_free: set[int] = set()
    ready_ops: set[int] = set()
    ready_alloc: set[int] = set()

    def add_ready(node_id: int) -> None:
        op = nodes[node_id].op
        if op == "FREE":
            ready_free.add(node_id)
        elif op == "ALLOC":
            ready_alloc.add(node_id)
        else:
            ready_ops.add(node_id)

    for node_id, degree in indegree.items():
        if degree == 0:
            add_ready(node_id)

    order: list[int] = []
    while ready_free or ready_ops or ready_alloc:
        pool = ready_free or ready_ops or ready_alloc
        node_id = min(pool)
        pool.discard(node_id)
        order.append(node_id)
        for dst in successors[node_id]:
            indegree[dst] -= 1
            if indegree[dst] == 0:
                add_ready(dst)

    if len(order) != len(nodes):
        raise ValueError("Input graph is not a DAG")
    return order


def _min_id_toposort(instance: ProblemInstance) -> list[int]:
    nodes = {node.id: node for node in instance.nodes}
    successors: dict[int, list[int]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in nodes}
    for edge in instance.edges:
        successors[edge.src].append(edge.dst)
        indegree[edge.dst] += 1
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


def _overflow_traffic(order: list[int], nodes: dict[int, Node]) -> int:
    """Predicted spill pressure: per-step normalized capacity overflow sum."""
    current = defaultdict(int)
    total = 0
    for node_id in order:
        node = nodes[node_id]
        if node.mem_type is None:
            continue
        if node.op == "ALLOC":
            current[node.mem_type] += node.size
        elif node.op == "FREE":
            current[node.mem_type] -= node.size
        cap = CACHE_CAPACITIES.get(node.mem_type, 1)
        over = current[node.mem_type] - cap
        if over > 0:
            total += over * NORM_CACHE_WEIGHT[node.mem_type]
    return total


# ---------------------------------------------------------------------------
# Memory-aware list scheduler (shared core, three priority variants)
# ---------------------------------------------------------------------------

def _memory_aware_order(instance: ProblemInstance, variant: str) -> list[int]:
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
    use_id_alloc_tiebreak = variant == "p1" and alloc_mem_types == {"L1", "L0B"} and any(
        node.op == "D2S" for node in instance.nodes
    )
    capfit = variant in {"capfit", "capfit_id"}
    weight = NORM_CACHE_WEIGHT if capfit else P1_CACHE_WEIGHT

    user_count: dict[int, int] = defaultdict(int)
    for node in instance.nodes:
        if node.op not in {"ALLOC", "FREE"}:
            for buf_id in node.bufs:
                user_count[buf_id] += 1

    current: dict[str, int] = defaultdict(int)
    ready_free: set[int] = set()
    ready_ops: set[int] = set()
    ready_alloc: set[int] = set()
    alloc_heap: list[tuple[int, ...]] = []
    order: list[int] = []

    def alloc_priority(node: Node) -> tuple[int, ...]:
        if variant == "capfit_id":
            return (node.id, node.id)
        buf_id = node.buf_id if node.buf_id is not None else -1
        waiters = user_count.get(buf_id, 0)
        successor_wait = min(
            (indegree[dst] for dst in successors[node.id] if nodes[dst].op != "FREE"),
            default=1_000_000,
        )
        if use_id_alloc_tiebreak:
            feeds_d2s = any(nodes[dst].op == "D2S" for dst in successors[node.id])
            ready_d2s = feeds_d2s and successor_wait <= 2
            feeds_transfer = variant == "p1" and successor_wait == 1 and any(
                nodes[dst].op in {"COPY_IN", "MOVE"} for dst in successors[node.id]
            )
            group = 0 if feeds_transfer else 1 if ready_d2s else 2
            return (group, successor_wait, 0, 0, node.id)
        alloc_pressure = node.size * weight.get(node.mem_type or "", 1)
        return (successor_wait, alloc_pressure, -waiters, node.size, node.id)

    def add_ready(node_id: int) -> None:
        node = nodes[node_id]
        if node.op == "FREE":
            ready_free.add(node_id)
        elif node.op == "ALLOC":
            ready_alloc.add(node_id)
            heapq.heappush(alloc_heap, alloc_priority(node))
        else:
            ready_ops.add(node_id)

    def free_priority(node: Node) -> tuple[int, int, int]:
        mem_type = node.mem_type or ""
        after = max(0, current[mem_type] - node.size)
        return (after * weight.get(mem_type, 1), node.size, node.id)

    def op_priority(node: Node) -> tuple[int, int, int, int]:
        released = sum(
            alloc_by_buf[b].size * weight.get(alloc_by_buf[b].mem_type or "", 1)
            for b in node.bufs
            if user_count.get(b) == 1 and b in alloc_by_buf
        )
        touched = sum(
            alloc_by_buf[b].size * weight.get(alloc_by_buf[b].mem_type or "", 1)
            for b in node.bufs
            if b in alloc_by_buf
        )
        return (-released, -touched, -node.cycles, node.id)

    for node_id, degree in indegree.items():
        if degree == 0:
            add_ready(node_id)

    while ready_free or ready_ops or ready_alloc:
        if ready_free:
            node_id = min(ready_free, key=lambda c: free_priority(nodes[c]))
            ready_free.remove(node_id)
        elif ready_ops:
            node_id = min(ready_ops, key=lambda c: op_priority(nodes[c]))
            ready_ops.remove(node_id)
        else:
            node_id = -1
            skipped: list[tuple[int, ...]] = []
            while alloc_heap:
                entry = heapq.heappop(alloc_heap)
                *priority, candidate = entry
                if candidate not in ready_alloc or tuple(priority) != alloc_priority(nodes[candidate])[:-1]:
                    continue
                node = nodes[candidate]
                cap = CACHE_CAPACITIES.get(node.mem_type or "", 1 << 30)
                if capfit and current[node.mem_type or ""] + node.size > cap:
                    skipped.append(entry)
                    continue
                node_id = candidate
                ready_alloc.remove(candidate)
                break
            if node_id < 0:
                if not skipped:
                    raise ValueError("ALLOC ready set is non-empty but heap is empty")
                # All ready ALLOCs overflow: force the one unblocking work soonest.
                best = min(
                    skipped,
                    key=lambda e: (
                        alloc_priority(nodes[e[-1]])[:1],
                        nodes[e[-1]].size * weight.get(nodes[e[-1]].mem_type or "", 1),
                        e[-1],
                    ),
                )
                node_id = best[-1]
                ready_alloc.remove(node_id)
                skipped = [e for e in skipped if e[-1] != node_id]
            for entry in skipped:
                heapq.heappush(alloc_heap, entry)

        node = nodes[node_id]
        order.append(node_id)

        if node.mem_type is not None:
            if node.op == "ALLOC":
                current[node.mem_type] += node.size
            elif node.op == "FREE":
                current[node.mem_type] = max(0, current[node.mem_type] - node.size)
        if node.op not in {"ALLOC", "FREE"}:
            for buf_id in node.bufs:
                if user_count[buf_id] > 0:
                    user_count[buf_id] -= 1

        for dst in sorted(successors[node_id]):
            indegree[dst] -= 1
            for pred in predecessors[dst]:
                if pred in ready_alloc:
                    heapq.heappush(alloc_heap, alloc_priority(nodes[pred]))
            if indegree[dst] == 0:
                add_ready(dst)

    if len(order) != len(nodes):
        raise ValueError("Input graph is not a DAG")
    return order


# ---------------------------------------------------------------------------
# Address assignment + spill insertion
# ---------------------------------------------------------------------------

class _BufState:
    __slots__ = ("buf_id", "size", "mem_type", "offset", "event_positions", "event_ptr")

    def __init__(self, buf_id: int, size: int, mem_type: str) -> None:
        self.buf_id = buf_id
        self.size = size
        self.mem_type = mem_type
        self.offset: int | None = None  # resident offset, None when spilled out
        self.event_positions: list[int] = []
        self.event_ptr = 0


class _FreeSpace:
    """Best-fit free interval manager for one cache type."""

    def __init__(self, capacity: int) -> None:
        self.free: list[tuple[int, int]] = [(0, capacity)]  # (offset, size)

    def find(self, size: int) -> int | None:
        for offset, free_size in sorted(self.free):
            if free_size >= size:
                return offset
        return None

    def alloc_at(self, offset: int, size: int) -> None:
        for index, (start, free_size) in enumerate(self.free):
            if start <= offset and offset + size <= start + free_size:
                self.free.pop(index)
                if offset > start:
                    self.free.append((start, offset - start))
                if start + free_size > offset + size:
                    self.free.append((offset + size, start + free_size - offset - size))
                return
        raise ValueError(f"alloc_at({offset}, {size}) outside free space")

    def release(self, offset: int, size: int) -> None:
        self.free.append((offset, size))
        self.free.sort()
        merged: list[tuple[int, int]] = []
        for start, length in self.free:
            if merged and merged[-1][0] + merged[-1][1] == start:
                merged[-1] = (merged[-1][0], merged[-1][1] + length)
            else:
                merged.append((start, length))
        self.free = merged


def _assign_memory_with_spills(
    instance: ProblemInstance,
    base_order: list[int],
    prefetch_window: int = 0,
) -> tuple[list[int], dict[int, int], list[tuple[int, int]]]:
    nodes = {node.id: node for node in instance.nodes}
    num_original = len(instance.nodes)
    position = {node_id: pos for pos, node_id in enumerate(base_order)}

    bufs: dict[int, _BufState] = {}
    for node in instance.nodes:
        if node.op == "ALLOC" and node.buf_id is not None:
            bufs[node.buf_id] = _BufState(node.buf_id, node.size, node.mem_type or "")
    for node in instance.nodes:
        if node.op not in {"ALLOC", "FREE"}:
            for buf_id in node.bufs:
                if buf_id in bufs:
                    bufs[buf_id].event_positions.append(position[node.id])
        elif node.op == "FREE" and node.buf_id in bufs:
            bufs[node.buf_id].event_positions.append(position[node.id])
    for state in bufs.values():
        state.event_positions.sort()

    copy_in_bufs = {b for n in instance.nodes if n.op == "COPY_IN" for b in n.bufs}
    space = {cache: _FreeSpace(cap) for cache, cap in CACHE_CAPACITIES.items()}
    resident: dict[str, set[int]] = defaultdict(set)
    memory: dict[int, int] = {}
    spill_entries: list[tuple[int, int]] = []
    spill_index_of_buf: dict[int, int] = {}
    order: list[int] = []

    def next_event(state: _BufState, pos: int) -> int:
        while state.event_ptr < len(state.event_positions) and state.event_positions[state.event_ptr] <= pos:
            state.event_ptr += 1
        if state.event_ptr < len(state.event_positions):
            return state.event_positions[state.event_ptr]
        return 1 << 60

    def spill_out(buf_id: int) -> None:
        state = bufs[buf_id]
        assert state.offset is not None
        space[state.mem_type].release(state.offset, state.size)
        resident[state.mem_type].discard(buf_id)
        state.offset = None
        spill_index_of_buf[buf_id] = len(spill_entries)
        spill_entries.append((buf_id, -1))
        order.append(num_original + 2 * (len(spill_entries) - 1))  # SPILL_OUT id

    def make_room(mem_type: str, size: int, pos: int, pinned: set[int]) -> int:
        offset = space[mem_type].find(size)
        relocations = 0
        while offset is None:
            victims = [b for b in resident[mem_type] if b not in pinned]
            if victims:
                def victim_score(b: int) -> tuple[float, int]:
                    dist = min(next_event(bufs[b], pos) - pos, 1 << 20)
                    cost = bufs[b].size if b in copy_in_bufs else 2 * bufs[b].size
                    return (dist * bufs[b].size / cost, bufs[b].size)

                victim = max(victims, key=victim_score)
                spill_out(victim)
            else:
                # Fragmentation among pinned buffers: relocate the smallest one
                # (legal spill + immediate reload before the consuming op runs).
                movable = sorted(
                    (b for b in resident[mem_type] if b in pinned),
                    key=lambda b: bufs[b].size,
                )
                relocations += 1
                if not movable or relocations > 100:
                    raise RuntimeError(f"No spill victim available in {mem_type}")
                buf = movable[0]
                spill_out(buf)
                reload(buf, pos, pinned - {buf})
            offset = space[mem_type].find(size)
        return offset

    def place(buf_id: int, pos: int, pinned: set[int]) -> int:
        state = bufs[buf_id]
        offset = make_room(state.mem_type, state.size, pos, pinned)
        space[state.mem_type].alloc_at(offset, state.size)
        state.offset = offset
        resident[state.mem_type].add(buf_id)
        return offset

    def reload(buf_id: int, pos: int, pinned: set[int]) -> None:
        offset = place(buf_id, pos, pinned)
        index = spill_index_of_buf.pop(buf_id)
        spill_entries[index] = (buf_id, offset)
        order.append(num_original + 2 * index + 1)  # SPILL_IN id

    for pos, node_id in enumerate(base_order):
        node = nodes[node_id]
        if node.op == "ALLOC" and node.buf_id is not None:
            offset = place(node.buf_id, pos, pinned={node.buf_id})
            memory[node.buf_id] = offset
            order.append(node_id)
        elif node.op == "FREE" and node.buf_id is not None:
            state = bufs[node.buf_id]
            if state.offset is None:
                reload(node.buf_id, pos, pinned={node.buf_id})
            space[state.mem_type].release(state.offset, state.size)
            resident[state.mem_type].discard(node.buf_id)
            state.offset = None
            order.append(node_id)
        else:
            needed = {b for b in node.bufs if b in bufs}
            for buf_id in sorted(needed):
                if bufs[buf_id].offset is None:
                    reload(buf_id, pos, pinned=needed)
            if prefetch_window:
                # Reload soon-needed spilled buffers early (no evictions) so
                # SPILL_IN latency overlaps compute instead of stalling users.
                for buf_id in list(spill_index_of_buf):
                    state = bufs[buf_id]
                    if (
                        next_event(state, pos) - pos <= prefetch_window
                        and space[state.mem_type].find(state.size) is not None
                    ):
                        reload(buf_id, pos, pinned=set())
            order.append(node_id)

    return order, memory, spill_entries
