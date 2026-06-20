"""Paper-experiment harness. Read-only wrt the promoted solver."""
from __future__ import annotations

import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ks_core import solver as INSTR
from ks_core.constants import CACHE_CAPACITIES as CAP
from ks_core.evaluator import compute_total_time
from ks_core.graph import load_json
from ks_core.io import read_schedule_txt
CASES = ["Conv_Case0", "Conv_Case1", "FlashAttention_Case0",
         "FlashAttention_Case1", "Matmul_Case0", "Matmul_Case1"]


def load_instance(case, problem_id):
    return load_json(ROOT / "data" / "raw" / "json" / f"{case}.json", problem_id=problem_id)


def clean_bufs(inst):
    return {b for n in inst.nodes if n.op == "COPY_IN" for b in n.bufs}


def random_topo(inst, seed):
    nodes = {n.id: n for n in inst.nodes}
    succ = defaultdict(list)
    indeg = {nid: 0 for nid in nodes}
    for e in inst.edges:
        succ[e.src].append(e.dst)
        indeg[e.dst] += 1
    rng = random.Random(seed)
    ready = [nid for nid, d in indeg.items() if d == 0]
    order = []
    while ready:
        i = rng.randrange(len(ready))
        ready[i], ready[-1] = ready[-1], ready[i]
        nid = ready.pop()
        order.append(nid)
        for d in succ[nid]:
            indeg[d] -= 1
            if indeg[d] == 0:
                ready.append(d)
    return order


def build_order(inst, name, case=None):
    if name in ("capfit_id", "p1", "capfit"):
        return INSTR._memory_aware_order(inst, variant=name)
    if name == "id_raw":
        return INSTR._id_raw_order(inst)
    if name == "min_id":
        return INSTR._min_id_toposort(inst)
    if name == "baseline":
        n = len(inst.nodes)
        sched = read_schedule_txt(
            ROOT / "results/exp001_baseline01/schedules" / f"P1_{case}_schedule.txt"
        )
        return [nid for nid in sched if nid < n]
    if name.startswith("random:"):
        return random_topo(inst, int(name.split(":")[1]))
    raise ValueError(name)


def assign(inst, order, victim_policy="dist_size_cost", prefetch_window=0):
    return INSTR._assign_memory_with_spills(
        inst, order, prefetch_window=prefetch_window, victim_policy=victim_policy
    )


def extra_split(spills, inst):
    alloc = {n.buf_id: n.size for n in inst.nodes if n.op == "ALLOC"}
    clean = clean_bufs(inst)
    cb = sum(alloc[b] for b, _ in spills if b in clean)
    db = sum(2 * alloc[b] for b, _ in spills if b not in clean)
    cc = sum(1 for b, _ in spills if b in clean)
    return {"extra": cb + db, "clean_bytes": cb, "dirty_bytes": db,
            "clean_count": cc, "dirty_count": len(spills) - cc, "spills": len(spills)}


def total_time(inst, order_with_spills, memory, spills):
    nodes = {n.id: n for n in inst.nodes}
    return compute_total_time(order_with_spills, nodes, inst.edges, memory=memory,
                              spill_entries=spills, num_original_nodes=len(inst.nodes))


def overflow_integral(order, inst):
    nodes = {n.id: n for n in inst.nodes}
    cur = defaultdict(int)
    total = 0.0
    for nid in order:
        n = nodes[nid]
        if n.mem_type is None:
            continue
        if n.op == "ALLOC":
            cur[n.mem_type] += n.size
        elif n.op == "FREE":
            cur[n.mem_type] -= n.size
        for c, cap in CAP.items():
            over = cur[c] - cap
            if over > 0:
                total += over / cap
    return total


def peak_working_set(order, inst):
    nodes = {n.id: n for n in inst.nodes}
    cur = defaultdict(int)
    peak = defaultdict(int)
    for nid in order:
        n = nodes[nid]
        if n.mem_type is None:
            continue
        if n.op == "ALLOC":
            cur[n.mem_type] += n.size
        elif n.op == "FREE":
            cur[n.mem_type] -= n.size
        for c in CAP:
            peak[c] = max(peak[c], cur[c])
    return dict(peak)


def live_clean_dirty_timeline(order, inst, mem_type="L1"):
    nodes = {n.id: n for n in inst.nodes}
    clean = clean_bufs(inst)
    live_clean = 0
    live_dirty = 0
    rows = []
    for pos, nid in enumerate(order):
        n = nodes[nid]
        if n.mem_type == mem_type and n.op == "ALLOC":
            if n.buf_id in clean:
                live_clean += n.size
            else:
                live_dirty += n.size
        elif n.mem_type == mem_type and n.op == "FREE":
            if n.buf_id in clean:
                live_clean -= n.size
            else:
                live_dirty -= n.size
        rows.append((pos, live_clean, live_dirty))
    return rows
