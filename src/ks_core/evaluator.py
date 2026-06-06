"""Evaluator for kernel scheduling solutions."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from ks_core.types import Edge, Node

CACHE_CAPACITIES = {"L1": 4096, "UB": 1024, "L0A": 256, "L0B": 256, "L0C": 512}
CACHE_TYPES = ("L1", "UB", "L0A", "L0B", "L0C")
L0_TYPES = ("L0A", "L0B", "L0C")


@dataclass(frozen=True)
class ResidencySegment:
    buf_id: int
    mem_type: str
    size: int
    offset: int
    start_node: int
    end_node: int
    start_pos: int
    end_pos: int

    @property
    def end_offset(self) -> int:
        return self.offset + self.size


def compute_max_vstay(order: list[int], nodes: dict[int, Node]) -> dict[str, int]:
    """Compute peak L1/UB size and peak L0 buffer counts."""
    current = {cache: 0 for cache in CACHE_TYPES}
    peak = {cache: 0 for cache in CACHE_TYPES}
    counts = {cache: 0 for cache in L0_TYPES}
    peak_counts = {cache: 0 for cache in L0_TYPES}

    for node_id in order:
        node = nodes.get(node_id)
        if node is None or node.mem_type is None:
            continue
        if node.op == "ALLOC":
            current[node.mem_type] += node.size
            peak[node.mem_type] = max(peak[node.mem_type], current[node.mem_type])
            if node.mem_type in counts:
                counts[node.mem_type] += 1
                peak_counts[node.mem_type] = max(peak_counts[node.mem_type], counts[node.mem_type])
        elif node.op == "FREE":
            current[node.mem_type] -= node.size
            if node.mem_type in counts:
                counts[node.mem_type] -= 1

    return {
        "max_L1": peak["L1"],
        "max_UB": peak["UB"],
        "max_L0A_count": peak_counts["L0A"],
        "max_L0B_count": peak_counts["L0B"],
        "max_L0C_count": peak_counts["L0C"],
    }


def validate_memory(
    order: list[int],
    nodes: dict[int, Node],
    memory: dict[int, int],
    capacities: dict[str, int] | None = None,
    spill_entries: list[tuple[int, int]] | None = None,
    num_original_nodes: int | None = None,
) -> list[str]:
    """Validate physical cache offsets and same-cache non-overlap."""
    capacities = capacities or CACHE_CAPACITIES
    allocs, _frees = _buffer_nodes(nodes)
    errors: list[str] = []

    missing = sorted(set(allocs) - set(memory))
    if missing:
        errors.append(f"Missing memory offsets: {missing[:10]} ({len(missing)} total)")

    for buf_id, alloc in allocs.items():
        if buf_id in memory:
            _check_offset(errors, buf_id, memory[buf_id], alloc.size, alloc.mem_type, capacities)

    for buf_id, offset in spill_entries or []:
        alloc = allocs.get(buf_id)
        if alloc is None:
            errors.append(f"Spill references unknown buffer {buf_id}")
            continue
        _check_offset(errors, buf_id, offset, alloc.size, alloc.mem_type, capacities)

    segments = _residency_segments(order, nodes, memory, spill_entries, num_original_nodes)
    for segment in segments:
        if segment.start_pos >= segment.end_pos:
            errors.append(
                f"Invalid residency segment for buffer {segment.buf_id}: "
                f"{segment.start_node}@{segment.start_pos} -> {segment.end_node}@{segment.end_pos}"
            )

    for mem_type in CACHE_TYPES:
        active: list[ResidencySegment] = []
        for segment in sorted(
            (s for s in segments if s.mem_type == mem_type),
            key=lambda s: (s.start_pos, s.end_pos),
        ):
            active = [s for s in active if s.end_pos > segment.start_pos]
            for other in active:
                if _overlap(segment.offset, segment.end_offset, other.offset, other.end_offset):
                    errors.append(
                        f"{mem_type} buffers {other.buf_id} [{other.offset},{other.end_offset}) "
                        f"and {segment.buf_id} [{segment.offset},{segment.end_offset}) overlap "
                        f"during [{segment.start_pos},{min(other.end_pos, segment.end_pos)})"
                    )
                    if len(errors) >= 50:
                        return errors + ["Too many memory validation errors; stopped early"]
            active.append(segment)

    return errors


def validate_spill(
    order: list[int],
    nodes: dict[int, Node],
    edges: list[Edge],
    spill_entries: list[tuple[int, int]],
    num_original_nodes: int,
) -> list[str]:
    """Validate spill node ids, schedule coverage, and spill dependency order."""
    errors: list[str] = []
    original_ids = set(nodes)
    spill_ids = {
        num_original_nodes + 2 * index + delta
        for index in range(len(spill_entries))
        for delta in (0, 1)
    }
    expected_ids = original_ids | spill_ids
    order_counts = Counter(order)
    order_set = set(order)

    missing = sorted(expected_ids - order_set)
    unknown = sorted(order_set - expected_ids)
    duplicates = sorted(node_id for node_id, count in order_counts.items() if count > 1)
    if missing:
        errors.append(f"Missing nodes: {missing[:10]} ({len(missing)} total)")
    if unknown:
        errors.append(f"Unknown nodes: {unknown[:10]} ({len(unknown)} total)")
    if duplicates:
        errors.append(f"Duplicate nodes: {duplicates[:10]} ({len(duplicates)} total)")

    position = {node_id: pos for pos, node_id in enumerate(order)}
    errors.extend(_edge_order_errors(edges, position, "Original DAG"))

    allocs, frees = _buffer_nodes(nodes)
    users_by_buf = _operation_users_by_buf(nodes)
    spills_by_buf: dict[int, list[tuple[int, int, int, int]]] = defaultdict(list)

    for index, (buf_id, _offset) in enumerate(spill_entries):
        out_id = num_original_nodes + 2 * index
        in_id = out_id + 1
        out_pos = position.get(out_id)
        in_pos = position.get(in_id)
        if out_pos is None or in_pos is None:
            continue
        if buf_id not in allocs or buf_id not in frees:
            errors.append(f"Spill {index + 1} references unknown buffer {buf_id}")
            continue

        label = f"Spill {index + 1} for buffer {buf_id}"
        alloc_pos = position.get(allocs[buf_id].id)
        free_pos = position.get(frees[buf_id].id)
        if alloc_pos is not None and alloc_pos >= out_pos:
            errors.append(f"{label}: ALLOC must precede SPILL_OUT")
        if out_pos >= in_pos:
            errors.append(f"{label}: SPILL_OUT must precede SPILL_IN")
        if free_pos is not None and in_pos >= free_pos:
            errors.append(f"{label}: SPILL_IN must precede FREE")

        blocked_users = [
            user_id
            for user_id in users_by_buf.get(buf_id, [])
            if out_pos < position.get(user_id, -1) < in_pos
        ]
        if blocked_users:
            errors.append(
                f"{label}: users between SPILL_OUT and SPILL_IN: "
                f"{blocked_users[:10]} ({len(blocked_users)} total)"
            )

        spills_by_buf[buf_id].append((out_pos, in_pos, out_id, in_id))

    for buf_id, buf_spills in spills_by_buf.items():
        for prev, current in zip(sorted(buf_spills), sorted(buf_spills)[1:]):
            if prev[1] >= current[0]:
                errors.append(
                    f"Buffer {buf_id} is spilled again before previous reload completes "
                    f"({prev[3]} -> {current[2]})"
                )

    return errors


def compute_extra(spill_entries: list[tuple[int, int]], nodes: dict[int, Node]) -> int:
    """Compute total extra DDR traffic from spill entries."""
    alloc_size = {node.buf_id: node.size for node in nodes.values() if node.op == "ALLOC"}
    copy_in_bufs = {buf for node in nodes.values() if node.op == "COPY_IN" for buf in node.bufs}
    return sum(
        alloc_size[buf_id] if buf_id in copy_in_bufs else 2 * alloc_size[buf_id]
        for buf_id, _offset in spill_entries
    )


def compute_total_time(
    order: list[int],
    nodes: dict[int, Node],
    edges: list[Edge],
    memory: dict[int, int] | None = None,
    spill_entries: list[tuple[int, int]] | None = None,
    num_original_nodes: int | None = None,
) -> int:
    """Compute total pipelined time for a fixed schedule order."""
    spill_entries = spill_entries or []
    num_original_nodes = num_original_nodes or _num_original_nodes(nodes)
    all_nodes = {**nodes, **_synthetic_spill_nodes(spill_entries, nodes, num_original_nodes)}
    position = {node_id: pos for pos, node_id in enumerate(order)}

    predecessors: dict[int, list[int]] = defaultdict(list)
    for edge in edges:
        predecessors[edge.dst].append(edge.src)
    for src, dst in _spill_edges(spill_entries, nodes, position, num_original_nodes):
        predecessors[dst].append(src)

    address_ready: dict[str, list[int]] = {}
    segments_by_start: dict[int, list[ResidencySegment]] = defaultdict(list)
    segments_by_end: dict[int, list[ResidencySegment]] = defaultdict(list)
    if memory is not None:
        address_ready = {cache: [0] * capacity for cache, capacity in CACHE_CAPACITIES.items()}
        for segment in _residency_segments(order, nodes, memory, spill_entries, num_original_nodes):
            segments_by_start[segment.start_node].append(segment)
            segments_by_end[segment.end_node].append(segment)

    end_time: dict[int, int] = {}
    pipe_ready: dict[str, int] = defaultdict(int)
    total = 0

    for node_id in order:
        node = all_nodes.get(node_id)
        if node is None:
            continue

        start = max((end_time.get(pred, 0) for pred in predecessors.get(node_id, [])), default=0)
        if node.pipe:
            start = max(start, pipe_ready[node.pipe])

        for segment in segments_by_start.get(node_id, []):
            ready = address_ready.get(segment.mem_type)
            if ready is not None and _offset_fits(
                segment.offset,
                segment.size,
                segment.mem_type,
                CACHE_CAPACITIES,
            ):
                start = max(start, max(ready[segment.offset:segment.end_offset], default=0))

        finish = start + node.cycles
        end_time[node_id] = finish
        total = max(total, finish)
        if node.pipe:
            pipe_ready[node.pipe] = finish

        for segment in segments_by_end.get(node_id, []):
            ready = address_ready.get(segment.mem_type)
            if ready is None or not _offset_fits(
                segment.offset,
                segment.size,
                segment.mem_type,
                CACHE_CAPACITIES,
            ):
                continue
            for offset in range(segment.offset, segment.end_offset):
                ready[offset] = max(ready[offset], finish)

    return total


def _buffer_nodes(nodes: dict[int, Node]) -> tuple[dict[int, Node], dict[int, Node]]:
    allocs = {
        node.buf_id: node
        for node in nodes.values()
        if node.op == "ALLOC" and node.buf_id is not None
    }
    frees = {
        node.buf_id: node
        for node in nodes.values()
        if node.op == "FREE" and node.buf_id is not None
    }
    return allocs, frees


def _operation_users_by_buf(nodes: dict[int, Node]) -> dict[int, list[int]]:
    users: dict[int, list[int]] = defaultdict(list)
    for node in nodes.values():
        if node.op in {"ALLOC", "FREE"}:
            continue
        for buf_id in node.bufs:
            users[buf_id].append(node.id)
    return users


def _num_original_nodes(nodes: dict[int, Node]) -> int:
    return max(nodes) + 1 if nodes else 0


def _check_offset(
    errors: list[str],
    buf_id: int,
    offset: int,
    size: int,
    mem_type: str | None,
    capacities: dict[str, int],
) -> None:
    if mem_type not in capacities:
        errors.append(f"Buffer {buf_id} has unknown cache type {mem_type}")
    elif offset < 0 or offset + size > capacities[mem_type]:
        errors.append(
            f"Buffer {buf_id} offset {offset} size {size} does not fit "
            f"{mem_type} capacity {capacities[mem_type]}"
        )


def _offset_fits(offset: int, size: int, mem_type: str, capacities: dict[str, int]) -> bool:
    return mem_type in capacities and offset >= 0 and offset + size <= capacities[mem_type]


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def _edge_order_errors(edges: list[Edge], position: dict[int, int], label: str) -> list[str]:
    errors: list[str] = []
    violations = 0
    for edge in edges:
        src_pos = position.get(edge.src)
        dst_pos = position.get(edge.dst)
        if src_pos is not None and dst_pos is not None and src_pos >= dst_pos:
            violations += 1
            if violations <= 5:
                errors.append(
                    f"{label} dependency violation: node {edge.src}@{src_pos} "
                    f"must precede node {edge.dst}@{dst_pos}"
                )
    if violations > 5:
        errors.append(f"{label} has {violations - 5} more dependency violations")
    return errors


def _residency_segments(
    order: list[int],
    nodes: dict[int, Node],
    memory: dict[int, int],
    spill_entries: list[tuple[int, int]] | None = None,
    num_original_nodes: int | None = None,
) -> list[ResidencySegment]:
    position = {node_id: pos for pos, node_id in enumerate(order)}
    allocs, frees = _buffer_nodes(nodes)
    num_original_nodes = num_original_nodes or _num_original_nodes(nodes)
    spills_by_buf: dict[int, list[tuple[int, int, int, int, int]]] = defaultdict(list)

    for index, (buf_id, new_offset) in enumerate(spill_entries or []):
        out_id = num_original_nodes + 2 * index
        in_id = out_id + 1
        if out_id in position and in_id in position:
            spills_by_buf[buf_id].append(
                (position[out_id], position[in_id], out_id, in_id, new_offset)
            )

    segments: list[ResidencySegment] = []
    for buf_id, alloc in allocs.items():
        free = frees.get(buf_id)
        if (
            free is None
            or buf_id not in memory
            or alloc.id not in position
            or free.id not in position
        ):
            continue

        start_node = alloc.id
        start_pos = position[alloc.id]
        offset = memory[buf_id]

        for _out_pos, _in_pos, out_id, in_id, new_offset in sorted(spills_by_buf.get(buf_id, [])):
            segments.append(
                ResidencySegment(
                    buf_id=buf_id,
                    mem_type=alloc.mem_type or "",
                    size=alloc.size,
                    offset=offset,
                    start_node=start_node,
                    end_node=out_id,
                    start_pos=start_pos,
                    end_pos=position[out_id],
                )
            )
            start_node = in_id
            start_pos = position[in_id]
            offset = new_offset

        segments.append(
            ResidencySegment(
                buf_id=buf_id,
                mem_type=alloc.mem_type or "",
                size=alloc.size,
                offset=offset,
                start_node=start_node,
                end_node=free.id,
                start_pos=start_pos,
                end_pos=position[free.id],
            )
        )

    return segments


def _synthetic_spill_nodes(
    spill_entries: list[tuple[int, int]],
    nodes: dict[int, Node],
    num_original_nodes: int,
) -> dict[int, Node]:
    allocs, _frees = _buffer_nodes(nodes)
    copy_in_bufs = {buf for node in nodes.values() if node.op == "COPY_IN" for buf in node.bufs}
    spill_nodes: dict[int, Node] = {}
    for index, (buf_id, _offset) in enumerate(spill_entries):
        size = allocs[buf_id].size if buf_id in allocs else 0
        reload_cycles = size * 2 + 150
        out_id = num_original_nodes + 2 * index
        in_id = out_id + 1
        spill_nodes[out_id] = Node(
            id=out_id,
            op="SPILL_OUT",
            pipe="MTE3",
            cycles=0 if buf_id in copy_in_bufs else reload_cycles,
            bufs=[buf_id],
        )
        spill_nodes[in_id] = Node(
            id=in_id,
            op="SPILL_IN",
            pipe="MTE2",
            cycles=reload_cycles,
            bufs=[buf_id],
        )
    return spill_nodes


def _spill_edges(
    spill_entries: list[tuple[int, int]],
    nodes: dict[int, Node],
    position: dict[int, int],
    num_original_nodes: int,
) -> list[tuple[int, int]]:
    allocs, frees = _buffer_nodes(nodes)
    users_by_buf = _operation_users_by_buf(nodes)
    edges: list[tuple[int, int]] = []
    spills_by_buf: dict[int, list[tuple[int, int, int, int]]] = defaultdict(list)

    for index, (buf_id, _offset) in enumerate(spill_entries):
        if buf_id not in allocs or buf_id not in frees:
            continue
        out_id = num_original_nodes + 2 * index
        in_id = out_id + 1
        out_pos = position.get(out_id)
        in_pos = position.get(in_id)
        if out_pos is None or in_pos is None:
            continue

        edges.extend([(allocs[buf_id].id, out_id), (out_id, in_id), (in_id, frees[buf_id].id)])
        for user_id in users_by_buf.get(buf_id, []):
            user_pos = position.get(user_id)
            if user_pos is None:
                continue
            if user_pos < out_pos:
                edges.append((user_id, out_id))
            elif user_pos > in_pos:
                edges.append((in_id, user_id))
        spills_by_buf[buf_id].append((out_pos, in_pos, out_id, in_id))

    for buf_spills in spills_by_buf.values():
        for prev, current in zip(sorted(buf_spills), sorted(buf_spills)[1:]):
            edges.append((prev[3], current[2]))

    return edges
