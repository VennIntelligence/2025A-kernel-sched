"""AutoResearch scratch: cost-aware topological-order search for P2.

All generators are case-agnostic and use only the input DAG and buffer metadata.
Official baseline schedules are loaded only in the final reporting path, never as
an input to an order generator.

See scripts/agent_cost_order_search.md for the full reproduction guide.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts" / "paper")]

import baselines as B  # noqa: E402
import harness as H  # noqa: E402

from ks_core import solver as S  # noqa: E402

OUT = ROOT / "results" / "autoresearch_v2" / "agent_cost_order"


def _critical_path(nodes, succ, topo):
    cp = {}
    for nid in reversed(topo):
        cp[nid] = int(nodes[nid].cycles or 0) + max(
            (cp[d] for d in succ[nid]), default=0
        )
    return cp


def _plain_topo(nodes, succ, indeg0):
    import heapq
    indeg = dict(indeg0)
    ready = [nid for nid, d in indeg.items() if d == 0]
    heapq.heapify(ready)
    out = []
    while ready:
        nid = heapq.heappop(ready)
        out.append(nid)
        for dst in succ[nid]:
            indeg[dst] -= 1
            if indeg[dst] == 0:
                heapq.heappush(ready, dst)
    return out


def cost_order(
    inst,
    *,
    dirty_weight: float = 2.0,
    release_mode: str = "sum",
    alloc_mode: str = "pressure",
    op_mode: str = "release",
    topk: int = 1,
    seed: int = 0,
) -> list[int]:
    """Cost-aware layered list scheduler.

    ``dirty_weight`` is the only semantic asymmetry: buffers replenished by a
    COPY_IN are one-way reloads while generated buffers require writeback plus
    reload. All other priorities are generic DAG/memory quantities.
    """
    nodes, succ, pred, indeg = graph(inst)
    topo = _plain_topo(nodes, succ, indeg)
    cp = _critical_path(nodes, succ, topo)
    clean = H.clean_bufs(inst)
    alloc = {n.buf_id: n for n in inst.nodes if n.op == "ALLOC" and n.buf_id is not None}
    remaining = defaultdict(int)
    for n in inst.nodes:
        if n.op not in {"ALLOC", "FREE"}:
            for b in n.bufs:
                if b in alloc:
                    remaining[b] += 1
    live = defaultdict(int)
    live_clean = defaultdict(int)
    live_dirty = defaultdict(int)
    ready_free: set[int] = set()
    ready_ops: set[int] = set()
    ready_alloc: set[int] = set()
    rng = random.Random(seed)

    def add_ready(nid):
        if nodes[nid].op == "FREE":
            ready_free.add(nid)
        elif nodes[nid].op == "ALLOC":
            ready_alloc.add(nid)
        else:
            ready_ops.add(nid)

    for nid, d in indeg.items():
        if d == 0:
            add_ready(nid)

    def buf_cost(b):
        a = alloc[b]
        cap = H.CAP.get(a.mem_type, 1)
        return a.size / cap * (1.0 if b in clean else dirty_weight)

    def release_parts(nid):
        c = d = 0.0
        raw = 0
        for b in nodes[nid].bufs:
            if b in alloc and remaining[b] == 1:
                v = alloc[b].size / H.CAP.get(alloc[b].mem_type, 1)
                raw += alloc[b].size
                if b in clean:
                    c += v
                else:
                    d += v
        return c, d, raw

    def touched(nid):
        return sum(buf_cost(b) for b in nodes[nid].bufs if b in alloc)

    def newly_ready(nid):
        # Static one-step frontier progress under the current indegrees.
        vals = [d for d in succ[nid] if indeg[d] == 1]
        return (
            sum(nodes[d].op == "FREE" for d in vals),
            sum(nodes[d].op not in {"FREE", "ALLOC"} for d in vals),
            len(vals),
        )

    def over_release(nid):
        score = 0.0
        for b in nodes[nid].bufs:
            if b not in alloc or remaining[b] != 1:
                continue
            a = alloc[b]
            cap = H.CAP.get(a.mem_type, 1)
            over = max(0, live[a.mem_type] - cap)
            score += min(a.size, over) / cap * (1 if b in clean else dirty_weight)
        return score

    def op_key(nid):
        c, d, raw = release_parts(nid)
        nf, no, na = newly_ready(nid)
        rel = c + dirty_weight * d
        if release_mode == "dirty_lex":
            primary = (-d, -c)
        elif release_mode == "over":
            primary = (-over_release(nid), -rel)
        elif release_mode == "raw_then_cost":
            primary = (-raw, -rel)
        else:
            primary = (-rel,)
        if op_mode == "frontier":
            rest = (-nf, -no, -na, -touched(nid), -cp[nid], nid)
        elif op_mode == "critical":
            rest = (-cp[nid], -touched(nid), -nf, -no, nid)
        elif op_mode == "dirty_touch":
            dirty_touch = sum(
                alloc[b].size / H.CAP.get(alloc[b].mem_type, 1)
                for b in nodes[nid].bufs if b in alloc and b not in clean
            )
            rest = (-dirty_touch, -touched(nid), -nf, -no, -cp[nid], nid)
        else:
            rest = (-touched(nid), -nf, -no, -cp[nid], nid)
        return primary + rest

    def alloc_key(nid):
        n = nodes[nid]
        b = n.buf_id
        is_clean = b in clean
        wait = min((indeg[d] for d in succ[nid] if nodes[d].op != "FREE"), default=10**9)
        cap = H.CAP.get(n.mem_type, 1)
        after = live[n.mem_type] + n.size
        over = max(0, after - cap)
        value = n.size / cap * (1 if is_clean else dirty_weight)
        if alloc_mode == "hardfit":
            return (1 if over else 0, wait, value, over / cap, nid)
        if alloc_mode == "hardfit_clean":
            return (1 if over else 0, wait, 0 if is_clean else 1, value, nid)
        if alloc_mode == "hardfit_dirty":
            return (1 if over else 0, wait, 0 if not is_clean else 1, value, nid)
        if alloc_mode == "clean_first":
            return (wait, 0 if is_clean else 1, over / cap, value, nid)
        if alloc_mode == "dirty_first":
            return (wait, 0 if not is_clean else 1, over / cap, value, nid)
        if alloc_mode == "cost":
            return (wait, value, over / cap, nid)
        if alloc_mode == "shield":
            # Under overflow, cheap clean allocations make preferable victims;
            # below capacity, keep allocations just-in-time by weighted size.
            return (wait, over / cap * (1 if is_clean else dirty_weight),
                    0 if (over and is_clean) else 1, value, nid)
        if alloc_mode == "frontier":
            unlock = sum(indeg[d] == 1 for d in succ[nid] if nodes[d].op != "FREE")
            return (wait, -unlock, value, over / cap, nid)
        return (wait, over / cap, value, nid)

    def choose(pool, key):
        ranked = sorted(pool, key=key)
        k = min(topk, len(ranked))
        return ranked[0] if k == 1 else ranked[rng.randrange(k)]

    order = []
    while ready_free or ready_ops or ready_alloc:
        if ready_free:
            nid = min(ready_free, key=lambda x: (-nodes[x].size, x))
            ready_free.remove(nid)
        elif ready_ops:
            nid = choose(ready_ops, op_key)
            ready_ops.remove(nid)
        else:
            nid = choose(ready_alloc, alloc_key)
            ready_alloc.remove(nid)
        n = nodes[nid]
        order.append(nid)
        if n.op == "ALLOC":
            live[n.mem_type] += n.size
            (live_clean if n.buf_id in clean else live_dirty)[n.mem_type] += n.size
        elif n.op == "FREE":
            live[n.mem_type] = max(0, live[n.mem_type] - n.size)
            target = live_clean if n.buf_id in clean else live_dirty
            target[n.mem_type] = max(0, target[n.mem_type] - n.size)
        else:
            for b in n.bufs:
                if b in alloc and remaining[b] > 0:
                    remaining[b] -= 1
        for dst in succ[nid]:
            indeg[dst] -= 1
            if indeg[dst] == 0:
                add_ready(dst)
    if len(order) != len(nodes):
        raise ValueError("not a DAG")
    return order


def p1_cost_order(
    inst,
    *,
    dirty_weight: float = 2.0,
    cache_mode: str = "p1",
    capfit: bool = False,
    alloc_cost: bool = False,
    dirty_lex: bool = False,
    semantic_tie: str = "none",
    tie_seed: int | None = None,
    tie_jitter: float | None = None,
    tie_cost_bias: float = 0.0,
) -> list[int]:
    """Minimal semantic ablation of the promoted memory-aware scheduler.

    The frontier mechanics and generic cache-pressure priorities are preserved;
    only release/touch value distinguishes generated (dirty) from COPY_IN-backed
    (clean) buffers. This isolates whether cost information in *ordering* helps.
    """
    import heapq

    nodes, succ, pred, indeg = graph(inst)
    clean = H.clean_bufs(inst)
    alloc = {n.buf_id: n for n in inst.nodes if n.op == "ALLOC" and n.buf_id is not None}
    weight = S.P1_CACHE_WEIGHT if cache_mode == "p1" else S.NORM_CACHE_WEIGHT
    tie_rng = random.Random(tie_seed)
    if tie_seed is not None and tie_jitter is None:
        tie = {nid: tie_rng.random() for nid in nodes}
    elif tie_seed is not None:
        tie = {nid: nid + tie_rng.uniform(-tie_jitter, tie_jitter) for nid in nodes}
    else:
        tie = {nid: float(nid) for nid in nodes}
    user_count = defaultdict(int)
    for n in inst.nodes:
        if n.op not in {"ALLOC", "FREE"}:
            for b in n.bufs:
                user_count[b] += 1

    alloc_mem_types = {n.mem_type for n in alloc.values()}
    use_id_alloc_tiebreak = (
        cache_mode == "p1" and alloc_mem_types == {"L1", "L0B"}
        and any(n.op == "D2S" for n in inst.nodes)
    )
    current = defaultdict(int)
    ready_free: set[int] = set()
    ready_ops: set[int] = set()
    ready_alloc: set[int] = set()
    alloc_heap = []

    def semantic(b):
        return 1.0 if b in clean else dirty_weight

    if tie_cost_bias:
        for nid, n in nodes.items():
            if n.op == "ALLOC" and n.buf_id in alloc:
                # Positive bias delays costly allocations (lifetime shortening).
                a = alloc[n.buf_id]
                tie[nid] += tie_cost_bias * semantic(n.buf_id) * a.size / H.CAP.get(a.mem_type, 1)
            elif n.op == "FREE" and n.buf_id in alloc:
                # The matching expensive FREE is pulled earlier where legal.
                a = alloc[n.buf_id]
                tie[nid] -= tie_cost_bias * semantic(n.buf_id) * a.size / H.CAP.get(a.mem_type, 1)

    def alloc_priority(n):
        b = n.buf_id if n.buf_id is not None else -1
        waiters = user_count.get(b, 0)
        successor_wait = min(
            (indeg[d] for d in succ[n.id] if nodes[d].op != "FREE"), default=10**9
        )
        if use_id_alloc_tiebreak:
            feeds_d2s = any(nodes[d].op == "D2S" for d in succ[n.id])
            ready_d2s = feeds_d2s and successor_wait <= 2
            feeds_transfer = successor_wait == 1 and any(
                nodes[d].op in {"COPY_IN", "MOVE"} for d in succ[n.id]
            )
            group = 0 if feeds_transfer else 1 if ready_d2s else 2
            if semantic_tie == "clean_first":
                sem = (0 if b in clean else 1, n.size * semantic(b))
            elif semantic_tie == "dirty_first":
                sem = (0 if b not in clean else 1, n.size * semantic(b))
            elif semantic_tie == "cost_small":
                sem = (n.size * semantic(b), 0)
            elif semantic_tie == "cost_large":
                sem = (-n.size * semantic(b), 0)
            else:
                sem = (0, 0)
            return (group, successor_wait, *sem, tie[n.id], n.id)
        pressure = n.size * weight.get(n.mem_type or "", 1)
        if alloc_cost:
            pressure *= semantic(b)
        return (successor_wait, pressure, -waiters, n.size, tie[n.id], n.id)

    def add_ready(nid):
        n = nodes[nid]
        if n.op == "FREE":
            ready_free.add(nid)
        elif n.op == "ALLOC":
            ready_alloc.add(nid)
            heapq.heappush(alloc_heap, alloc_priority(n))
        else:
            ready_ops.add(nid)

    def free_priority(n):
        after = max(0, current[n.mem_type or ""] - n.size)
        return (after * weight.get(n.mem_type or "", 1), n.size, tie[n.id], n.id)

    def op_priority(n):
        clean_rel = sum(
            alloc[b].size * weight.get(alloc[b].mem_type or "", 1)
            for b in n.bufs if b in alloc and b in clean and user_count.get(b) == 1
        )
        dirty_rel = sum(
            alloc[b].size * weight.get(alloc[b].mem_type or "", 1)
            for b in n.bufs if b in alloc and b not in clean and user_count.get(b) == 1
        )
        touched = sum(
            alloc[b].size * weight.get(alloc[b].mem_type or "", 1) * semantic(b)
            for b in n.bufs if b in alloc
        )
        if dirty_lex:
            return (-dirty_rel, -clean_rel, -touched, -n.cycles, tie[n.id], n.id)
        return (-(clean_rel + dirty_weight * dirty_rel), -touched, -n.cycles,
                tie[n.id], n.id)

    for nid, d in indeg.items():
        if d == 0:
            add_ready(nid)
    order = []
    while ready_free or ready_ops or ready_alloc:
        if ready_free:
            nid = min(ready_free, key=lambda x: free_priority(nodes[x]))
            ready_free.remove(nid)
        elif ready_ops:
            nid = min(ready_ops, key=lambda x: op_priority(nodes[x]))
            ready_ops.remove(nid)
        else:
            nid = -1
            skipped = []
            while alloc_heap:
                entry = heapq.heappop(alloc_heap)
                candidate = entry[-1]
                if (
                    candidate not in ready_alloc
                    or entry[:-1] != alloc_priority(nodes[candidate])[:-1]
                ):
                    continue
                n = nodes[candidate]
                cap = H.CAP.get(n.mem_type or "", 1 << 30)
                if capfit and current[n.mem_type or ""] + n.size > cap:
                    skipped.append(entry)
                    continue
                nid = candidate
                ready_alloc.remove(candidate)
                break
            if nid < 0:
                if not skipped:
                    raise RuntimeError("empty alloc heap")
                best = min(
                    skipped,
                    key=lambda e: (
                        alloc_priority(nodes[e[-1]])[:1],
                        nodes[e[-1]].size
                        * weight.get(nodes[e[-1]].mem_type or "", 1),
                        e[-1],
                    ),
                )
                nid = best[-1]
                ready_alloc.remove(nid)
                skipped = [e for e in skipped if e[-1] != nid]
            for entry in skipped:
                heapq.heappush(alloc_heap, entry)
        n = nodes[nid]
        order.append(nid)
        if n.mem_type is not None:
            if n.op == "ALLOC":
                current[n.mem_type] += n.size
            elif n.op == "FREE":
                current[n.mem_type] = max(0, current[n.mem_type] - n.size)
        if n.op not in {"ALLOC", "FREE"}:
            for b in n.bufs:
                if user_count[b] > 0:
                    user_count[b] -= 1
        for dst in succ[nid]:
            indeg[dst] -= 1
            for p in pred[dst]:
                if p in ready_alloc:
                    heapq.heappush(alloc_heap, alloc_priority(nodes[p]))
            if indeg[dst] == 0:
                add_ready(dst)
    return order


def cost_unlock_order(
    inst,
    *,
    band: int = 1,
    group_mode: str = "cheap",
    member_mode: str = "clean_first",
    op_mode: str = "weighted_release",
    dirty_weight: float = 2.0,
    free_mode: str = "lifo",
) -> list[int]:
    """Cost-aware unlock-frontier scheduler.

    The underlying locality rule is the generic ready-predecessor grouping used
    by ``_unlock_frontier_order``. Within a bounded structural-ID band, choices
    use the asymmetric 1x clean / 2x generated-buffer traffic model. Scheduling
    clean allocations first also makes them available as cheaper victims when
    the remainder of the consumer group is materialized.
    """
    import heapq

    nodes, succ, pred, indeg = graph(inst)
    clean = H.clean_bufs(inst)
    alloc = {n.buf_id: n for n in inst.nodes if n.op == "ALLOC" and n.buf_id is not None}
    remaining = defaultdict(int)
    for n in inst.nodes:
        if n.op not in {"ALLOC", "FREE"}:
            for b in n.bufs:
                if b in alloc:
                    remaining[b] += 1
    ready_free: set[int] = set()
    ready_ops: set[int] = set()
    ready_alloc: set[int] = set()
    heap = []

    def sem(b):
        return 1.0 if b in clean else dirty_weight

    def norm_buf(b):
        a = alloc[b]
        return a.size / H.CAP.get(a.mem_type, 1) * sem(b)

    def unlock_targets(nid):
        vals = []
        for dst in succ[nid]:
            if nodes[dst].op == "FREE" or indeg[dst] <= 0:
                continue
            if sum(p in ready_alloc for p in pred[dst]) == indeg[dst]:
                vals.append(dst)
        return vals

    def target_stats(dst):
        group = [p for p in pred[dst] if p in ready_alloc]
        clean_cost = dirty_cost = 0.0
        for p in group:
            b = nodes[p].buf_id
            if b not in alloc:
                continue
            v = nodes[p].size / H.CAP.get(nodes[p].mem_type, 1)
            if b in clean:
                clean_cost += v
            else:
                dirty_cost += v * dirty_weight
        release_clean = release_dirty = 0.0
        for b in nodes[dst].bufs:
            if b in alloc and remaining[b] == 1:
                v = alloc[b].size / H.CAP.get(alloc[b].mem_type, 1)
                if b in clean:
                    release_clean += v
                else:
                    release_dirty += v * dirty_weight
        return clean_cost, dirty_cost, release_clean, release_dirty

    def alloc_key(nid):
        targets = unlock_targets(nid)
        if not targets:
            return ((1 << 60), 0, 0, 0, nid)
        target = min(targets)
        bucket = target // max(1, band)
        cc, dc, rc, rd = target_stats(target)
        if group_mode == "cheap":
            group = (dc + cc, dc, -rd, -rc)
        elif group_mode == "clean_reserve":
            group = (-cc, dc, -rd, -rc)
        elif group_mode == "dirty_finish":
            group = (-rd, -rc, dc, cc)
        elif group_mode == "dirty_group":
            group = (-dc, cc, -rd, -rc)
        else:
            group = (0, 0, 0, 0)
        b = nodes[nid].buf_id
        if member_mode == "clean_first":
            member = (0 if b in clean else 1, norm_buf(b) if b in alloc else 0)
        elif member_mode == "dirty_first":
            member = (0 if b not in clean else 1, norm_buf(b) if b in alloc else 0)
        elif member_mode == "cost_small":
            member = (norm_buf(b) if b in alloc else 0, 0)
        else:
            member = (0, 0)
        return (bucket, *group, target, *member, nid)

    def refresh(nid):
        for dst in succ[nid]:
            for p in pred[dst]:
                if p in ready_alloc:
                    heapq.heappush(heap, (alloc_key(p), p))

    def add_ready(nid):
        n = nodes[nid]
        if n.op == "FREE":
            ready_free.add(nid)
        elif n.op == "ALLOC":
            ready_alloc.add(nid)
            heapq.heappush(heap, (alloc_key(nid), nid))
            refresh(nid)
        else:
            ready_ops.add(nid)

    def op_key(nid):
        n = nodes[nid]
        rc = rd = 0.0
        tc = td = 0.0
        for b in n.bufs:
            if b not in alloc:
                continue
            v = alloc[b].size / H.CAP.get(alloc[b].mem_type, 1)
            if b in clean:
                tc += v
                if remaining[b] == 1:
                    rc += v
            else:
                td += v * dirty_weight
                if remaining[b] == 1:
                    rd += v * dirty_weight
        bucket = nid // max(1, band)
        if op_mode == "dirty_lex":
            return (bucket, -rd, -rc, -td, -tc, nid)
        if op_mode == "weighted_release":
            return (bucket, -(rd + rc), -(td + tc), nid)
        if op_mode == "dirty_touch":
            return (bucket, -td, -rd, -tc, -rc, nid)
        return (bucket, nid)

    for nid, d in indeg.items():
        if d == 0:
            add_ready(nid)
    order = []
    while ready_free or ready_ops or ready_alloc:
        if ready_free:
            if free_mode == "cost":
                nid = min(ready_free, key=lambda x: (
                    0 if nodes[x].buf_id not in clean else 1,
                    -nodes[x].size * sem(nodes[x].buf_id), -x,
                ))
            else:
                nid = max(ready_free)
            ready_free.remove(nid)
        elif ready_ops:
            nid = min(ready_ops, key=op_key)
            ready_ops.remove(nid)
        else:
            while heap:
                key, cand = heapq.heappop(heap)
                if cand in ready_alloc and key == alloc_key(cand):
                    nid = cand
                    ready_alloc.remove(nid)
                    break
            else:
                for cand in ready_alloc:
                    heapq.heappush(heap, (alloc_key(cand), cand))
                continue
        n = nodes[nid]
        order.append(nid)
        if n.op not in {"ALLOC", "FREE"}:
            for b in n.bufs:
                if b in alloc and remaining[b] > 0:
                    remaining[b] -= 1
        for dst in succ[nid]:
            indeg[dst] -= 1
            for p in pred[dst]:
                if p in ready_alloc:
                    heapq.heappush(heap, (alloc_key(p), p))
            if indeg[dst] == 0:
                add_ready(dst)
    return order


def graph(inst):
    nodes = {n.id: n for n in inst.nodes}
    succ = defaultdict(list)
    pred = defaultdict(list)
    indeg = {nid: 0 for nid in nodes}
    for e in inst.edges:
        if e.src in nodes and e.dst in nodes:
            succ[e.src].append(e.dst)
            pred[e.dst].append(e.src)
            indeg[e.dst] += 1
    for x in succ.values():
        x.sort()
    for x in pred.values():
        x.sort()
    return nodes, succ, pred, indeg


def inspect_case(case: str) -> None:
    inst = H.load_instance(case, 2)
    nodes, succ, pred, indeg = graph(inst)
    clean = H.clean_bufs(inst)
    alloc = {n.buf_id: n for n in inst.nodes if n.op == "ALLOC"}
    print(case, "nodes", len(nodes), "clean", len(clean))
    for n in inst.nodes[:120]:
        bs = [
            f"{b}:{alloc[b].mem_type}/{alloc[b].size}/{'C' if b in clean else 'D'}"
            for b in n.bufs if b in alloc
        ]
        print(n.id, n.op, n.mem_type, n.buf_id, n.size, "bufs", bs,
              "pred", pred[n.id], "succ", succ[n.id])


def cost_overflow_integral(order, inst):
    """Optimistic lower-bound surrogate: evict live clean bytes before dirty."""
    nodes = {n.id: n for n in inst.nodes}
    clean = H.clean_bufs(inst)
    c = defaultdict(int)
    d = defaultdict(int)
    total = 0.0
    dirty_part = 0.0
    for nid in order:
        n = nodes[nid]
        if n.mem_type is not None and n.op in {"ALLOC", "FREE"}:
            target = c if n.buf_id in clean else d
            target[n.mem_type] += n.size if n.op == "ALLOC" else -n.size
        for cache, cap in H.CAP.items():
            over = max(0, c[cache] + d[cache] - cap)
            cheap = min(c[cache], over)
            costly = over - cheap
            total += (cheap + 2 * costly) / cap
            dirty_part += costly / cap
    return total, dirty_part


def variant_grid(full: bool = False):
    rows = []
    weights = (1.5, 2.0, 3.0, 4.0) if full else (2.0, 3.0)
    releases = ("sum", "dirty_lex", "over", "raw_then_cost") if full else ("sum", "dirty_lex")
    allocs = ("pressure", "cost", "clean_first", "dirty_first", "shield", "frontier",
              "hardfit", "hardfit_clean", "hardfit_dirty") if full else (
                  "hardfit", "hardfit_clean", "hardfit_dirty")
    ops = ("release", "frontier", "critical", "dirty_touch") if full else ("release", "frontier")
    for w in weights:
        for r in releases:
            for a in allocs:
                for o in ops:
                    rows.append((f"cw{w:g}_{r}_{a}_{o}", dict(
                        dirty_weight=w, release_mode=r, alloc_mode=a, op_mode=o
                    )))
    # Fixed-seed stochastic frontier variants are algorithmic multi-starts,
    # never derived from a reference schedule.
    if full:
        for seed in range(8):
            rows.append((f"cw2_sum_pressure_release_top2_s{seed}", dict(
                dirty_weight=2.0, release_mode="sum", alloc_mode="pressure",
                op_mode="release", topk=2, seed=seed,
            )))
    return rows


def proxy_screen(cases, full: bool) -> None:
    out = []
    variants = variant_grid(full)
    for case in cases:
        inst = H.load_instance(case, 2)
        ref = S._id_raw_order(inst)
        ref_pos = {nid: p for p, nid in enumerate(ref)}
        for name, kwargs in variants:
            t0 = time.perf_counter()
            order = cost_order(inst, **kwargs)
            wc, wd = cost_overflow_integral(order, inst)
            pos = {nid: p for p, nid in enumerate(order)}
            row = {
                "case": case, "variant": name, "weighted_phi": wc,
                "dirty_phi": wd, "phi": H.overflow_integral(order, inst),
                "peak": H.peak_working_set(order, inst),
                "mean_abs_pos_from_id_raw": sum(abs(pos[n] - ref_pos[n]) for n in pos) / len(pos),
                "order_seconds": time.perf_counter() - t0,
            }
            print(case, name, f"wphi={wc:.3f}", f"dphi={wd:.3f}",
                  f"sec={row['order_seconds']:.3f}", flush=True)
            out.append(row)
    path = OUT / "proxy_screen.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", path)


def actual_measure(inst, order, policy="dist_size_cost"):
    t0 = time.perf_counter()
    try:
        order_ws, memory, spills = H.assign(inst, order, victim_policy=policy, prefetch_window=0)
        meta = {"fallback": False, "policy": policy}
    except RuntimeError as exc:
        try:
            order_ws, memory, spills, smeta = B.safe_assign(
                inst, order, victim_policy=policy, prefetch_window=0, timeout_seconds=20
            )
            meta = {"fallback": smeta["fallback"], "policy": smeta["victim_policy"],
                    "error": str(exc)}
        except RuntimeError as final:
            return {"extra": math.inf, "clean_bytes": math.inf, "dirty_bytes": math.inf,
                    "clean_count": -1, "dirty_count": -1, "spills": -1,
                    "time": math.inf, "time_source": "failed", "fallback": True,
                    "policy": policy, "error": str(final),
                    "wall_seconds": time.perf_counter() - t0}
    split = H.extra_split(spills, inst)
    tt, time_source = B.controlled_total_time(inst, order_ws, memory, spills)
    return {**split, "time": tt, "time_source": time_source,
            "wall_seconds": time.perf_counter() - t0, **meta}


def actual_probe(cases) -> None:
    specs = [
        ("current_capfit_id", lambda i: S._memory_aware_order(i, "capfit_id")),
        ("current_p1", lambda i: S._memory_aware_order(i, "p1")),
        ("current_id_raw", S._id_raw_order),
        ("blind_pressure_uniform", B.pressure_uniform),
    ]
    for w in (1.25, 1.5, 2.0, 3.0, 4.0, 8.0):
        for cache_mode in ("p1", "norm"):
            for capfit in (False, True):
                for dirty_lex in (False, True):
                    name = f"p1cost_w{w:g}_{cache_mode}_cap{int(capfit)}_lex{int(dirty_lex)}"
                    specs.append((name, lambda i, w=w, cache_mode=cache_mode,
                                  capfit=capfit, dirty_lex=dirty_lex: p1_cost_order(
                                      i, dirty_weight=w, cache_mode=cache_mode,
                                      capfit=capfit, dirty_lex=dirty_lex)))
    rows = []
    for case in cases:
        inst = H.load_instance(case, 2)
        for name, fn in specs:
            t0 = time.perf_counter()
            order = fn(inst)
            order_sec = time.perf_counter() - t0
            m = actual_measure(inst, order)
            row = {"case": case, "variant": name, "order_seconds": order_sec, **m}
            rows.append(row)
            print(case, name, "extra", m["extra"], "spills", m["spills"],
                  f"order={order_sec:.3f}s assign={m['wall_seconds']:.3f}s", flush=True)
    path = OUT / "actual_probe.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("wrote", path)


def multistart(cases, seeds: int) -> None:
    rows = []
    semantic_modes = ("none", "clean_first", "dirty_first", "cost_small", "cost_large")
    for case in cases:
        inst = H.load_instance(case, 2)
        best = None
        for mode in semantic_modes:
            for seed in range(seeds):
                t0 = time.perf_counter()
                order = p1_cost_order(
                    inst, dirty_weight=2.0, cache_mode="p1", capfit=False,
                    semantic_tie=mode, tie_seed=seed,
                )
                order_sec = time.perf_counter() - t0
                m = actual_measure(inst, order)
                row = {"case": case, "variant": f"p1multi_{mode}_s{seed}",
                       "semantic_tie": mode, "seed": seed,
                       "order_seconds": order_sec, **m}
                rows.append(row)
                key = (m["extra"], m["spills"], m["time"])
                if best is None or key < best[0]:
                    best = (key, row)
                    print("NEW BEST", case, row["variant"], key,
                          f"order={order_sec:.3f}s assign={m['wall_seconds']:.3f}s",
                          flush=True)
        print("FINAL BEST", case, best[1], flush=True)
        path = OUT / "multistart_partial.json"
        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    path = OUT / "multistart.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("wrote", path)


def local_multistart(cases, seeds: int) -> None:
    rows = []
    jitters = (0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256)
    biases = (0.0, 1.0, 4.0, 16.0, 64.0)
    for case in cases:
        inst = H.load_instance(case, 2)
        base = S._memory_aware_order(inst, "p1")
        bm = actual_measure(inst, base)
        best = ((bm["extra"], bm["spills"], bm["time"]), {"variant": "current_p1", **bm})
        print("START BEST", case, best[0], flush=True)
        for jitter in jitters:
            for bias in biases:
                for seed in range(seeds):
                    t0 = time.perf_counter()
                    order = p1_cost_order(
                        inst, dirty_weight=2.0, cache_mode="p1", capfit=False,
                        semantic_tie="none", tie_seed=seed, tie_jitter=jitter,
                        tie_cost_bias=bias,
                    )
                    order_sec = time.perf_counter() - t0
                    m = actual_measure(inst, order)
                    row = {"case": case,
                           "variant": f"p1local_j{jitter:g}_b{bias:g}_s{seed}",
                           "jitter": jitter, "cost_bias": bias, "seed": seed,
                           "order_seconds": order_sec, **m}
                    rows.append(row)
                    key = (m["extra"], m["spills"], m["time"])
                    if key < best[0]:
                        best = (key, row)
                        print("NEW BEST", case, row["variant"], key, flush=True)
            (OUT / "local_multistart_partial.json").write_text(
                json.dumps(rows, indent=2), encoding="utf-8"
            )
        print("FINAL BEST", case, best[1], flush=True)
    path = OUT / "local_multistart.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("wrote", path)


def fast_key(inst, order):
    try:
        _ow, _mem, spills = H.assign(
            inst, order, victim_policy="dist_size_cost", prefetch_window=0
        )
    except RuntimeError:
        return (math.inf, math.inf), None
    split = H.extra_split(spills, inst)
    return (split["extra"], split["spills"]), split


def fast_key_with_policy(inst, order, policy):
    try:
        _ow, _mem, spills = H.assign(
            inst, order, victim_policy=policy, prefetch_window=0
        )
    except RuntimeError:
        return (math.inf, math.inf), None
    split = H.extra_split(spills, inst)
    return (split["extra"], split["spills"]), split


def assign_detail(inst, order):
    try:
        ow, mem, spills = H.assign(
            inst, order, victim_policy="dist_size_cost", prefetch_window=0
        )
    except RuntimeError:
        return (math.inf, math.inf), None
    split = H.extra_split(spills, inst)
    return (split["extra"], split["spills"]), (ow, mem, spills, split)


def assign_detail_with_policy(inst, order, policy):
    try:
        ow, mem, spills = H.assign(inst, order, victim_policy=policy, prefetch_window=0)
    except RuntimeError:
        return (math.inf, math.inf), None
    split = H.extra_split(spills, inst)
    return (split["extra"], split["spills"]), (ow, mem, spills, split)


def initial_search_order(inst):
    """Generic cost-objective portfolio; no reference schedules are consulted."""
    candidates = [
        ("capfit_id", S._memory_aware_order(inst, "capfit_id")),
        ("p1", S._memory_aware_order(inst, "p1")),
        ("id_raw", S._id_raw_order(inst)),
    ]
    for seed in range(32):
        candidates.append((f"local_j1_s{seed}", p1_cost_order(
            inst, dirty_weight=2.0, cache_mode="p1", capfit=False,
            tie_seed=seed, tie_jitter=1.0,
        )))
    best = None
    for name, order in candidates:
        key, split = fast_key(inst, order)
        if best is None or key < best[0]:
            best = (key, name, order, split)
    return best


def _move_proposal(inst, order, pred, succ, rng):
    nodes = {n.id: n for n in inst.nodes}
    clean = H.clean_bufs(inst)
    alloc = {n.buf_id: n for n in inst.nodes if n.op == "ALLOC" and n.buf_id is not None}
    pos = {nid: i for i, nid in enumerate(order)}

    # Cost-biased proposal population: generated-buffer events are sampled more
    # often because each avoidable residence/spill byte costs twice a clean one.
    nid = order[rng.randrange(len(order))]
    for _ in range(4):
        cand = order[rng.randrange(len(order))]
        n = nodes[cand]
        dirty_bytes = sum(alloc[b].size for b in n.bufs if b in alloc and b not in clean)
        if n.buf_id in alloc and n.buf_id not in clean:
            dirty_bytes += n.size
        if rng.random() < min(0.9, 0.15 + dirty_bytes / 4096):
            nid = cand
            break

    i = pos[nid]
    earliest = max((pos[p] + 1 for p in pred[nid]), default=0)
    latest = min((pos[d] - 1 for d in succ[nid]), default=len(order) - 1)
    if earliest >= latest or (i == earliest and i == latest):
        return None
    n = nodes[nid]
    radius = rng.choice((1, 2, 4, 8, 16, 32, 64, 128, 256))
    lo = max(earliest, i - radius)
    hi = min(latest, i + radius)
    if lo == hi:
        return None

    dirty_event = (
        (n.buf_id in alloc and n.buf_id not in clean)
        or any(b in alloc and b not in clean for b in n.bufs)
    )
    if n.op == "ALLOC":
        prefer_later = True  # delay materialization / shorten live range
    elif n.op == "FREE":
        prefer_later = False
    elif dirty_event and rng.random() < 0.7:
        # Pull costly consumers toward readiness; this can unlock their FREEs.
        prefer_later = False
    else:
        prefer_later = rng.random() < 0.5
    choices = (
        list(range(max(i + 1, lo), hi + 1))
        if prefer_later
        else list(range(lo, min(i, hi + 1)))
    )
    if not choices:
        choices = [j for j in range(lo, hi + 1) if j != i]
    if not choices:
        return None
    # Log-like step distribution: most moves are local, with occasional escape.
    j = min(choices, key=lambda x: abs(x - i)) if rng.random() < 0.35 else rng.choice(choices)
    proposal = list(order)
    proposal.pop(i)
    proposal.insert(j, nid)
    return proposal


def hillclimb(cases, iters: int, seed: int) -> None:
    summary = []
    for case in cases:
        inst = H.load_instance(case, 2)
        nodes, succ, pred, _indeg = graph(inst)
        init_key, init_name, current, init_split = initial_search_order(inst)
        current_key = init_key
        best_order = list(current)
        best_key = current_key
        rng = random.Random(seed)
        accepted = 0
        t0 = time.perf_counter()
        print("HILL START", case, init_name, init_key, flush=True)
        trace = [{"iteration": 0, "key": list(init_key), "source": init_name}]
        for iteration in range(1, iters + 1):
            proposal = _move_proposal(inst, current, pred, succ, rng)
            if proposal is None:
                continue
            key, split = fast_key(inst, proposal)
            if key < current_key:
                current = proposal
                current_key = key
                accepted += 1
                if key < best_key:
                    best_key = key
                    best_order = list(proposal)
                    trace.append({"iteration": iteration, "key": list(key),
                                  "accepted": accepted})
                    print("HILL BEST", case, iteration, key, "accepted", accepted,
                          flush=True)
            if iteration % 500 == 0:
                print("HILL PROGRESS", case, iteration, best_key,
                      f"sec={time.perf_counter()-t0:.1f}", flush=True)
                (OUT / f"hill_{case}_order.json").write_text(
                    json.dumps(best_order), encoding="utf-8"
                )
        final = actual_measure(inst, best_order)
        ok, reason = B.validate_topological_order(inst, best_order)
        row = {"case": case, "initial": init_name, "initial_key": list(init_key),
               "iterations": iters, "seed": seed, "accepted": accepted,
               "valid_topological": ok, "validation_reason": reason,
               "wall_seconds": time.perf_counter() - t0, "trace": trace,
               **final}
        summary.append(row)
        (OUT / f"hill_{case}_order.json").write_text(
            json.dumps(best_order), encoding="utf-8"
        )
        (OUT / "hill_summary_partial.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        print("HILL FINAL", row, flush=True)
    (OUT / "hill_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _relocate(order, nid, j):
    i = order.index(nid)
    if i == j:
        return None
    p = list(order)
    p.pop(i)
    p.insert(j, nid)
    return p


def _targeted_proposals(inst, order, detail, limit):
    ow, _mem, spills, _split = detail
    n_orig = len(inst.nodes)
    nodes, succ, pred, _indeg = graph(inst)
    clean = H.clean_bufs(inst)
    alloc = {n.buf_id: n for n in inst.nodes if n.op == "ALLOC" and n.buf_id is not None}
    pos = {nid: i for i, nid in enumerate(order)}
    events = defaultdict(list)
    for n in inst.nodes:
        if n.op not in {"ALLOC", "FREE"}:
            for b in n.bufs:
                if b in alloc:
                    events[b].append((pos[n.id], n.id))
        elif n.buf_id in alloc:
            events[n.buf_id].append((pos[n.id], n.id))
    for vals in events.values():
        vals.sort()

    spill_pos = {}
    base_pos = 0
    for x in ow:
        if x < n_orig:
            base_pos += 1
        elif (x - n_orig) % 2 == 0:
            spill_pos[(x - n_orig) // 2] = base_pos

    ranked = []
    for idx, (b, _off) in enumerate(spills):
        if b not in alloc:
            continue
        cost = alloc[b].size * (1 if b in clean else 2)
        ranked.append((-cost, 0 if b not in clean else 1, idx, b, spill_pos.get(idx, 0)))
    ranked.sort()
    proposals = []
    seen = set()

    def try_move(nid, destinations):
        i = pos[nid]
        earliest = max((pos[p] + 1 for p in pred[nid]), default=0)
        latest = min((pos[d] - 1 for d in succ[nid]), default=len(order) - 1)
        for j in destinations:
            j = max(earliest, min(latest, int(j)))
            if j == i:
                continue
            key = (nid, j)
            if key not in seen:
                seen.add(key)
                proposals.append((nid, j, _relocate(order, nid, j)))

    for _negcost, _dirtyrank, idx, b, sp in ranked[:limit]:
        vals = events[b]
        next_items = [(p, nid) for p, nid in vals if p >= sp]
        prev_items = [(p, nid) for p, nid in vals if p < sp]
        if next_items:
            p, nid = next_items[0]
            earliest = max((pos[x] + 1 for x in pred[nid]), default=0)
            try_move(nid, (earliest, sp, (earliest + p) // 2, p - 1, p - 4, p - 16))
            # If the consumer itself is pinned by late predecessors, pull those
            # predecessors (and one ancestor level) forward generically.
            for q in sorted(pred[nid], key=lambda x: pos[x], reverse=True)[:3]:
                qe = max((pos[x] + 1 for x in pred[q]), default=0)
                try_move(q, (qe, sp, (qe + pos[q]) // 2, pos[q] - 4, pos[q] - 16))
                for a in sorted(pred[q], key=lambda x: pos[x], reverse=True)[:2]:
                    ae = max((pos[x] + 1 for x in pred[a]), default=0)
                    try_move(a, (ae, sp, (ae + pos[a]) // 2))
        if prev_items:
            p, nid = prev_items[-1]
            latest = min((pos[x] - 1 for x in succ[nid]), default=len(order) - 1)
            try_move(nid, (latest, sp - 1, (p + latest) // 2, p + 1, p + 4, p + 16))
    return proposals


def targeted_search(cases, rounds: int, beam: int) -> None:
    summary = []
    for case in cases:
        inst = H.load_instance(case, 2)
        init_key, init_name, order, _ = initial_search_order(inst)
        current_key, detail = assign_detail(inst, order)
        trace = [{"round": 0, "key": list(current_key), "source": init_name}]
        start = time.perf_counter()
        print("TARGET START", case, init_name, current_key, flush=True)
        for round_id in range(1, rounds + 1):
            candidates = _targeted_proposals(inst, order, detail, beam)
            best = None
            for nid, j, proposal in candidates:
                if proposal is None:
                    continue
                key, candidate_detail = assign_detail(inst, proposal)
                if key < current_key and (best is None or key < best[0]):
                    best = (key, proposal, candidate_detail, nid, j)
            if best is None:
                print("TARGET STUCK", case, round_id, current_key,
                      "proposals", len(candidates), flush=True)
                break
            current_key, order, detail, nid, j = best
            trace.append({"round": round_id, "key": list(current_key),
                          "moved_node": nid, "destination": j,
                          "proposals": len(candidates)})
            print("TARGET BEST", case, round_id, current_key, "move", nid, j,
                  "candidates", len(candidates), flush=True)
            (OUT / f"targeted_{case}_order.json").write_text(
                json.dumps(order), encoding="utf-8"
            )
        final = actual_measure(inst, order)
        ok, reason = B.validate_topological_order(inst, order)
        row = {"case": case, "initial": init_name, "initial_key": list(init_key),
               "rounds_requested": rounds, "beam": beam, "trace": trace,
               "search_wall_seconds": time.perf_counter() - start,
               "valid_topological": ok, "validation_reason": reason, **final}
        summary.append(row)
        (OUT / f"targeted_{case}_order.json").write_text(json.dumps(order), encoding="utf-8")
        (OUT / "targeted_summary_partial.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        print("TARGET FINAL", row, flush=True)
    (OUT / "targeted_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def current_portfolio_order(inst, policy="share_adaptive_25"):
    candidates = [
        ("unlock_frontier", S._unlock_frontier_order(inst)),
        ("capfit_id", S._memory_aware_order(inst, "capfit_id")),
        ("p1", S._memory_aware_order(inst, "p1")),
        ("id_raw", S._id_raw_order(inst)),
    ]
    best = None
    for name, order in candidates:
        key, split = fast_key_with_policy(inst, order, policy)
        if best is None or key < best[0]:
            best = (key, name, order, split)
    return best


def unlock_hill(cases, iters: int, seed: int) -> None:
    """Exact cost-aware local search around the structure-only portfolio."""
    policy = "share_adaptive_25"
    summary = []
    for case in cases:
        inst = H.load_instance(case, 2)
        nodes, succ, pred, _ = graph(inst)
        current_key, source, current, _ = current_portfolio_order(inst, policy)
        best_order = list(current)
        best_key = current_key
        rng = random.Random(seed)
        trace = [{"iteration": 0, "key": list(best_key), "source": source}]
        accepted = 0
        started = time.perf_counter()
        print("UH START", case, source, current_key, flush=True)
        for iteration in range(1, iters + 1):
            proposal = _move_proposal(inst, current, pred, succ, rng)
            if proposal is None:
                continue
            key, _split = fast_key_with_policy(inst, proposal, policy)
            if key < current_key:
                current_key = key
                current = proposal
                accepted += 1
                if key < best_key:
                    best_key = key
                    best_order = list(proposal)
                    trace.append({"iteration": iteration, "key": list(key),
                                  "accepted": accepted})
                    print("UH BEST", case, iteration, key, flush=True)
            if iteration % 1000 == 0:
                print("UH PROGRESS", case, iteration, best_key,
                      f"sec={time.perf_counter()-started:.1f}", flush=True)
                (OUT / f"unlock_hill_{case}_order.json").write_text(
                    json.dumps(best_order), encoding="utf-8"
                )
        final = actual_measure(inst, best_order, policy)
        ok, reason = B.validate_topological_order(inst, best_order)
        row = {"case": case, "source": source, "initial_key": list(trace[0]["key"]),
               "iterations": iters, "seed": seed, "accepted": accepted,
               "trace": trace, "search_wall_seconds": time.perf_counter() - started,
               "valid_topological": ok, "validation_reason": reason, **final}
        summary.append(row)
        (OUT / f"unlock_hill_{case}_order.json").write_text(
            json.dumps(best_order), encoding="utf-8"
        )
        (OUT / "unlock_hill_summary_partial.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        print("UH FINAL", row, flush=True)
    (OUT / "unlock_hill_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


def unlock_targeted(cases, rounds: int, beam: int) -> None:
    policy = "share_adaptive_25"
    summary = []
    for case in cases:
        inst = H.load_instance(case, 2)
        initial_key, source, order, _ = current_portfolio_order(inst, policy)
        current_key, detail = assign_detail_with_policy(inst, order, policy)
        trace = [{"round": 0, "key": list(current_key), "source": source}]
        started = time.perf_counter()
        print("UT START", case, source, current_key, flush=True)
        for round_id in range(1, rounds + 1):
            proposals = _targeted_proposals(inst, order, detail, beam)
            best = None
            for nid, j, proposal in proposals:
                key, cd = assign_detail_with_policy(inst, proposal, policy)
                if key < current_key and (best is None or key < best[0]):
                    best = (key, proposal, cd, nid, j)
            if best is None:
                print("UT STUCK", case, round_id, current_key, len(proposals), flush=True)
                break
            current_key, order, detail, nid, j = best
            trace.append({"round": round_id, "key": list(current_key),
                          "moved_node": nid, "destination": j,
                          "proposals": len(proposals)})
            print("UT BEST", case, round_id, current_key, nid, j, flush=True)
        final = actual_measure(inst, order, policy)
        ok, reason = B.validate_topological_order(inst, order)
        row = {"case": case, "source": source, "initial_key": list(initial_key),
               "rounds": rounds, "beam": beam, "trace": trace,
               "search_wall_seconds": time.perf_counter() - started,
               "valid_topological": ok, "validation_reason": reason, **final}
        summary.append(row)
        (OUT / f"unlock_targeted_{case}_order.json").write_text(
            json.dumps(order), encoding="utf-8"
        )
        (OUT / "unlock_targeted_summary_partial.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        print("UT FINAL", row, flush=True)
    (OUT / "unlock_targeted_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


def spill_report(cases) -> None:
    reports = []
    for case in cases:
        inst = H.load_instance(case, 2)
        key, name, order, _ = initial_search_order(inst)
        key, detail = assign_detail(inst, order)
        ow, _mem, spills, split = detail
        alloc = {n.buf_id: n for n in inst.nodes if n.op == "ALLOC"}
        clean = H.clean_bufs(inst)
        counts = Counter(b for b, _ in spills)
        by_size = Counter((alloc[b].mem_type, alloc[b].size,
                           "clean" if b in clean else "dirty") for b, _ in spills)
        by_buf = sorted((count * alloc[b].size * (1 if b in clean else 2), b,
                         count, alloc[b].size, alloc[b].mem_type,
                         "clean" if b in clean else "dirty")
                        for b, count in counts.items())
        row = {"case": case, "source": name, "key": list(key), "split": split,
               "spill_by_size": [list(x) + [count] for x, count in by_size.most_common()],
               "top_buffers": [list(x) for x in reversed(by_buf[-40:])]}
        reports.append(row)
        print(json.dumps(row, indent=2), flush=True)
    (OUT / "spill_report.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")


def policy_probe(cases) -> None:
    rows = []
    for case in cases:
        inst = H.load_instance(case, 2)
        candidates = [("capfit_id", S._memory_aware_order(inst, "capfit_id")),
                      ("p1", S._memory_aware_order(inst, "p1")),
                      ("id_raw", S._id_raw_order(inst))]
        if hasattr(S, "_unlock_frontier_order"):
            candidates.append(("unlock_frontier", S._unlock_frontier_order(inst)))
        best_init = initial_search_order(inst)
        candidates.append((best_init[1], best_init[2]))
        for oname, order in candidates:
            for policy in ("dist_size_cost", "cost_then_dist", "cheap_first",
                           "far_only", "size_only", "share_adaptive_25"):
                m = actual_measure(inst, order, policy)
                row = {"case": case, "order": oname, "policy_requested": policy, **m}
                rows.append(row)
                print(case, oname, policy, m["extra"], m["spills"], flush=True)
    (OUT / "policy_probe.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


def unlock_grid(cases, full: bool) -> None:
    rows = []
    bands = (1, 4, 16, 64, 256) if full else (1, 16, 64)
    groups = ("cheap", "clean_reserve", "dirty_finish", "dirty_group")
    members = ("clean_first", "dirty_first", "cost_small", "id") if full else (
        "clean_first", "dirty_first")
    ops = ("weighted_release", "dirty_lex", "dirty_touch", "id") if full else (
        "weighted_release", "dirty_lex")
    for case in cases:
        inst = H.load_instance(case, 2)
        seen = {}
        best = None
        ref = S._unlock_frontier_order(inst)
        refm = actual_measure(inst, ref, "share_adaptive_25")
        print("UNLOCK REF", case, refm["extra"], refm["spills"], flush=True)
        for band in bands:
            for gm in groups:
                for mm in members:
                    for om in ops:
                        name = f"costunlock_b{band}_{gm}_{mm}_{om}"
                        t0 = time.perf_counter()
                        order = cost_unlock_order(
                            inst, band=band, group_mode=gm, member_mode=mm,
                            op_mode=om, dirty_weight=2.0,
                        )
                        order_sec = time.perf_counter() - t0
                        sig = hash(tuple(order))
                        if sig in seen:
                            continue
                        seen[sig] = name
                        m = actual_measure(inst, order, "share_adaptive_25")
                        row = {"case": case, "variant": name, "band": band,
                               "group_mode": gm, "member_mode": mm, "op_mode": om,
                               "order_seconds": order_sec, **m}
                        rows.append(row)
                        key = (m["extra"], m["spills"], m["time"])
                        if best is None or key < best[0]:
                            best = (key, row)
                            print("UNLOCK BEST", case, name, key, "unique", len(seen),
                                  flush=True)
        print("UNLOCK FINAL", case, best[1], "unique", len(seen), flush=True)
        (OUT / "unlock_grid_partial.json").write_text(
            json.dumps(rows, indent=2), encoding="utf-8"
        )
    (OUT / "unlock_grid.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


def final_eval() -> None:
    """Freeze the best independently-found orders, then compare post hoc."""
    official_rows = json.loads(
        (ROOT / "results" / "exp001_baseline01" / "metrics.json").read_text()
    )
    old_metrics = (
        ROOT
        / "results"
        / "autoresearch"
        / "iter038_id_raw_candidate"
        / "metrics.json"
    )
    old_rows = json.loads(old_metrics.read_text())
    official = {r["case"]: r for r in official_rows if r["problem"] == 2}
    old = {r["case"]: r for r in old_rows if r["problem"] == 2}
    search_files = {
        "Conv_Case0": OUT / "unlock_hill_Conv_Case0_order.json",
        "Conv_Case1": OUT / "unlock_targeted_Conv_Case1_order.json",
    }
    search_meta = {
        "Conv_Case0": "cost-aware exact local search (10,000 proposals, seed 0)",
        "Conv_Case1": "cost-aware spill-frontier search (beam 10, 2 rounds)",
    }
    rows = []
    chosen_orders = {}
    for case in H.CASES:
        inst = H.load_instance(case, 2)
        blind_key, blind_name, blind_order, _ = current_portfolio_order(inst)
        candidates = [(blind_key, "cost-aware search: no improving move", blind_order)]
        path = search_files.get(case)
        if path and path.exists():
            order = json.loads(path.read_text())
            key, _ = fast_key_with_policy(inst, order, "share_adaptive_25")
            candidates.append((key, search_meta[case], order))
        chosen_key, method, chosen = min(candidates, key=lambda x: x[0])
        chosen_orders[case] = chosen
        ours = actual_measure(inst, chosen, "share_adaptive_25")
        blind = actual_measure(inst, blind_order, "share_adaptive_25")
        ok, reason = B.validate_topological_order(inst, chosen)
        row = {
            "case": case,
            "method": method,
            "valid_topological": ok,
            "validation_reason": reason,
            "cost_search_extra": ours["extra"],
            "cost_search_clean_bytes": ours["clean_bytes"],
            "cost_search_dirty_bytes": ours["dirty_bytes"],
            "cost_search_spills": ours["spills"],
            "cost_search_time": ours["time"],
            "strong_blind_order": blind_name,
            "strong_blind_extra": blind["extra"],
            "strong_blind_spills": blind["spills"],
            "delta_vs_strong_blind": ours["extra"] - blind["extra"],
            "official_baseline_extra": official[case]["extra"],
            "delta_vs_official": ours["extra"] - official[case]["extra"],
            "old_iter038_extra": old[case]["extra"],
            "delta_vs_old_iter038": ours["extra"] - old[case]["extra"],
        }
        rows.append(row)
        print("FINAL", row, flush=True)

    fields = list(rows[0])
    with (OUT / "final_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    summary = {
        "concurrent_solver_note": (
            "Evaluated against the shared round-5 working tree containing "
            "unlock_frontier, best-fit free-space selection, and share_adaptive_25."
        ),
        "algorithm_constraint": (
            "No official-baseline schedule is read by any generator/search. "
            "Official metrics are loaded only here after order selection."
        ),
        "policy": "share_adaptive_25 for both searched and strong cost-blind orders",
        "rows": rows,
    }
    (OUT / "final_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = [
        "# Cost-aware order-search findings",
        "",
        summary["concurrent_solver_note"],
        "",
        summary["algorithm_constraint"],
        "",
        "The only robust gain over the new structure-only unlock frontier came from "
        "bounded exact-cost local search. It advances dependency chains associated "
        "with expensive spill events; the accepted Conv0/Conv1 moves pull a clean "
        "ALLOC/COPY_IN chain earlier, changing the live clean reserve and avoiding "
        "dirty writeback/reload traffic.",
        "",
        "| Case | Cost search | Strong blind | Official | Delta vs blind |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        report.append(
            f"| {r['case']} | {r['cost_search_extra']:,} | "
            f"{r['strong_blind_extra']:,} | {r['official_baseline_extra']:,} | "
            f"{r['delta_vs_strong_blind']:+,} |"
        )
    report += [
        "",
        "## Failed directions",
        "",
        "- Global clean-first/dirty-first allocation priorities destroyed locality, "
        "often increasing traffic by an order of magnitude.",
        "- Merely weighting last-use release by 1x/2x produced the same order on most "
        "frontiers; the semantic signal rarely broke a real choice.",
        "- Capacity/overflow surrogates correlated poorly with exact spill traffic; "
        "low overflow could still choose expensive victims or fragment the allocator.",
        "- Random tie-breaking and unguided block moves mostly regressed; useful moves "
        "were sparse and concentrated around exact spill frontiers.",
        "",
        "## Interpretation",
        "",
        "A defensible revised method is a two-level optimizer: a structure-only "
        "unlock-frontier schedule provides locality, then a bounded asymmetric-cost "
        "repair pass proposes topologically legal moves around observed spill events "
        "and keeps a move only if exact 1x-clean/2x-dirty traffic improves. This is "
        "genuinely cost-aware in ordering, unlike the former candidate portfolio, but "
        "the gains beyond the strong structural scheduler are concentrated in Conv.",
    ]
    (OUT / "findings.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["inspect", "proxy", "probe", "multistart",
                                         "local_multistart", "hillclimb", "targeted",
                                         "spill_report", "policy_probe", "unlock_grid",
                                         "unlock_hill", "unlock_targeted", "final"])
    parser.add_argument("--case", default="Conv_Case0")
    parser.add_argument("--cases", nargs="*")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--iters", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--beam", type=int, default=200)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.mode == "inspect":
        inspect_case(args.case)
    elif args.mode == "proxy":
        proxy_screen(args.cases or H.CASES, args.full)
    elif args.mode == "probe":
        actual_probe(args.cases or ["Conv_Case0", "FlashAttention_Case0", "FlashAttention_Case1"])
    elif args.mode == "multistart":
        multistart(args.cases or H.CASES, args.seeds)
    elif args.mode == "local_multistart":
        local_multistart(args.cases or H.CASES, args.seeds)
    elif args.mode == "hillclimb":
        hillclimb(args.cases or H.CASES, args.iters, args.seed)
    elif args.mode == "targeted":
        targeted_search(args.cases or H.CASES, args.rounds, args.beam)
    elif args.mode == "spill_report":
        spill_report(args.cases or H.CASES)
    elif args.mode == "policy_probe":
        policy_probe(args.cases or H.CASES)
    elif args.mode == "unlock_grid":
        unlock_grid(args.cases or H.CASES, args.full)
    elif args.mode == "unlock_hill":
        unlock_hill(args.cases or H.CASES, args.iters, args.seed)
    elif args.mode == "unlock_targeted":
        unlock_targeted(args.cases or H.CASES, args.rounds, args.beam)
    elif args.mode == "final":
        final_eval()


if __name__ == "__main__":
    main()
