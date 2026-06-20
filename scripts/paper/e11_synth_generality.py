"""E11 (C1 generality) — synthetic capacity-bound DAG.

Builds a small GEMM-style accumulation kernel whose L1 working set exceeds
capacity under every schedule (mandatory overflow, like Matmul_Case1), then
shows that the *cost* of that mandatory overflow is governed by clean/dirty
spill composition — i.e. spill-cost-aware liveness shaping (C1) generalizes
beyond the six contest cases, on a different tile geometry (512/256 B tiles).

Two artifacts:
  * Controlled ablation: identical DAG structure, reserve buffers loaded via
    COPY_IN (clean) vs produced by a compute op (dirty). Same schedule, same
    spill count, same peak -> extra doubles for the dirty reserve.
  * Order sweep: on the clean instance, scheduler orders that preserve the
    clean reserve resident at the overflow window pay far less than naive /
    random topological orders.

Read-only wrt the promoted solver. Writes:
  data/processed/synthetic/Synthetic_Case0_{clean,dirty}.json
  results/paper/e11_synth_ablation.csv
  results/paper/e11_synth_orders.csv
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "paper"))

from ks_core.evaluator import validate_memory, validate_spill  # noqa: E402
from ks_core.graph import load_json  # noqa: E402

import harness as H  # noqa: E402

PARAMS = dict(G=7, SW=512, R=10, SA=512, SX=256)
SYNTH_DIR = ROOT / "data" / "processed" / "synthetic"
RESULTS = ROOT / "results" / "paper"
SWEEP_SEEDS = 30
SOLVER_ORDERS = ["capfit_id", "p1", "id_raw", "min_id"]


def build(params: dict, dirty_reserve: bool) -> dict:
    G, SW, R, SA, SX = (params[k] for k in ("G", "SW", "R", "SA", "SX"))
    nodes: list[dict] = []
    edges: list[list[int]] = []
    nid = 0
    bid = 0

    def new_node(d: dict) -> int:
        nonlocal nid
        d["Id"] = nid
        nodes.append(d)
        nid += 1
        return d["Id"]

    def new_buf() -> int:
        nonlocal bid
        b = bid
        bid += 1
        return b

    def alloc(buf, size, mem="L1"):
        return new_node({"Op": "ALLOC", "BufId": buf, "Size": size, "Type": mem})

    def free(buf, size, mem="L1"):
        return new_node({"Op": "FREE", "BufId": buf, "Size": size, "Type": mem})

    def copy_in(buf):
        return new_node({"Op": "COPY_IN", "Bufs": [buf], "Cycles": 100, "Pipe": "MTE2"})

    def op(name, bufs, cycles, pipe):
        return new_node({"Op": name, "Bufs": list(bufs), "Cycles": cycles, "Pipe": pipe})

    # weights: rotating reuse, long-lived; clean (COPY_IN) or dirty (compute)
    w_buf, w_alloc, w_ready = [], {}, {}
    w_users: dict[int, list[int]] = defaultdict(list)
    for _ in range(G):
        b = new_buf()
        w_buf.append(b)
        a = alloc(b, SW)
        w_alloc[b] = a
        if dirty_reserve:
            ready = op("VEC", [b], 100, "VECTOR")
        else:
            ready = copy_in(b)
        edges.append([a, ready])
        w_ready[b] = ready
        w_users[b].append(ready)

    # accumulator chain: acc_r reads acc_{r-1} -> consecutive accs co-resident
    prev_acc = prev_mm = prev_acc_alloc = None
    for r in range(R):
        xb = new_buf()
        xa = alloc(xb, SX)
        xc = copy_in(xb)
        edges.append([xa, xc])

        ab = new_buf()
        aa = alloc(ab, SA)
        wsel = w_buf[r % G]
        reads = [ab, wsel, xb] + ([prev_acc] if prev_acc is not None else [])
        mm = op("MATMUL", reads, 200, "CUBE")
        edges.append([aa, mm])
        edges.append([xc, mm])
        edges.append([w_ready[wsel], mm])
        w_users[wsel].append(mm)
        if prev_acc is not None:
            edges.append([prev_mm, mm])

        xf = free(xb, SX)
        edges.append([mm, xf])
        edges.append([xc, xf])
        if prev_acc is not None:
            af = free(prev_acc, SA)
            edges.append([mm, af])
            edges.append([prev_acc_alloc, af])
        prev_acc, prev_mm, prev_acc_alloc = ab, mm, aa

    co = op("COPY_OUT", [prev_acc], 150, "MTE3")
    edges.append([prev_mm, co])
    fa = free(prev_acc, SA)
    edges.append([co, fa])
    edges.append([prev_acc_alloc, fa])

    for b in w_buf:
        f = free(b, SW)
        edges.append([w_alloc[b], f])
        for u in w_users[b]:
            edges.append([u, f])

    return {"Nodes": nodes, "Edges": edges}


def validate(inst) -> list[str]:
    ids = H.build_order(inst, "capfit_id")
    ows, mem, sp = H.assign(inst, ids, "dist_size_cost", 0)
    nodes = {n.id: n for n in inst.nodes}
    errs = validate_memory(ows, nodes, mem, spill_entries=sp,
                           num_original_nodes=len(inst.nodes))
    errs += validate_spill(ows, nodes, inst.edges, sp, len(inst.nodes))
    return errs


def measure(inst, name):
    ids = H.build_order(inst, name)
    _, _, sp = H.assign(inst, ids, "dist_size_cost", 0)
    d = H.extra_split(sp, inst)
    tl = H.live_clean_dirty_timeline(ids, inst, "L1")
    _, pc, pd = max(tl, key=lambda t: t[1] + t[2])
    peak = pc + pd
    return {
        "order": name, "extra": d["extra"], "clean_bytes": d["clean_bytes"],
        "dirty_bytes": d["dirty_bytes"], "spills": d["spills"],
        "peak_total": peak, "peak_clean": pc, "peak_dirty": pd,
        "clean_frac_at_peak": (pc / peak) if peak else 0.0,
    }


def main() -> None:
    SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    paths = {}
    insts = {}
    for kind, dirty in (("clean", False), ("dirty", True)):
        data = build(PARAMS, dirty_reserve=dirty)
        p = SYNTH_DIR / f"Synthetic_Case0_{kind}.json"
        p.write_text(json.dumps(data))
        paths[kind] = p
        insts[kind] = load_json(p, problem_id=2)

    failures = []
    for kind, inst in insts.items():
        errs = validate(inst)
        if errs:
            failures.append(f"{kind}: {errs[:5]}")
            print(f"VALIDATION ERRORS ({kind}): {errs[:5]}")
        else:
            print(f"validate OK: {kind} (N={len(inst.nodes)})")

    # ---- controlled ablation: clean vs dirty reserve, matched orders ----
    abl_rows = []
    for kind, inst in insts.items():
        for name in SOLVER_ORDERS:
            row = measure(inst, name)
            row["reserve"] = kind
            abl_rows.append(row)
    abl_cols = ["reserve", "order", "extra", "clean_bytes", "dirty_bytes",
                "spills", "peak_total", "peak_clean", "peak_dirty"]
    with (RESULTS / "e11_synth_ablation.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=abl_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(abl_rows)

    # ---- order sweep on the clean instance ----
    sweep_rows = []
    for name in SOLVER_ORDERS + [f"random:{s}" for s in range(SWEEP_SEEDS)]:
        try:
            row = measure(insts["clean"], name)
        except Exception as exc:  # noqa: BLE001
            print(f"SKIP {name}: {exc}")
            continue
        row["family"] = "scheduler" if name in SOLVER_ORDERS else "random"
        sweep_rows.append(row)
    sweep_cols = ["order", "family", "extra", "clean_bytes", "dirty_bytes",
                  "spills", "peak_total", "peak_clean", "peak_dirty",
                  "clean_frac_at_peak"]
    with (RESULTS / "e11_synth_orders.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sweep_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sweep_rows)

    # ---- capacity-bound check (min working set over swept orders / cap) ----
    min_peak = min(r["peak_total"] for r in sweep_rows)
    cap = H.CAP["L1"]
    ratio = min_peak / cap

    # ---- assertions ----
    clean_capfit = next(r for r in abl_rows if r["reserve"] == "clean" and r["order"] == "capfit_id")
    dirty_capfit = next(r for r in abl_rows if r["reserve"] == "dirty" and r["order"] == "capfit_id")
    print("\n--- ablation (capfit_id) ---")
    print(f"clean: extra={clean_capfit['extra']} spills={clean_capfit['spills']} peak={clean_capfit['peak_total']}")
    print(f"dirty: extra={dirty_capfit['extra']} spills={dirty_capfit['spills']} peak={dirty_capfit['peak_total']}")
    print(f"capacity-bound: min_peak={min_peak} cap={cap} ratio={ratio:.4f}")
    best_sched = min(r["extra"] for r in sweep_rows if r["family"] == "scheduler")
    best_rand = min(r["extra"] for r in sweep_rows if r["family"] == "random")
    print(f"clean sweep: best scheduler extra={best_sched}  best random extra={best_rand}")

    asserts = []
    if dirty_capfit["extra"] != 2 * clean_capfit["extra"]:
        asserts.append(f"expected dirty==2x clean, got {dirty_capfit['extra']} vs {clean_capfit['extra']}")
    if dirty_capfit["spills"] != clean_capfit["spills"]:
        asserts.append("expected matched spill counts clean vs dirty")
    if ratio <= 1.0:
        asserts.append(f"expected capacity-bound ratio>1, got {ratio:.4f}")
    if best_sched >= best_rand:
        asserts.append("expected scheduler orders to beat random orders")
    if failures:
        asserts.append(f"instance validation failed: {failures}")
    for a in asserts:
        print(f"ASSERTION FAILED E11: {a}")
    if not asserts:
        print("ASSERTION PASS E11: 2x clean/dirty, capacity-bound, scheduler<random")
    print(f"DONE E11: {paths['clean']}, {paths['dirty']}, "
          f"{RESULTS / 'e11_synth_ablation.csv'}, {RESULTS / 'e11_synth_orders.csv'}")


if __name__ == "__main__":
    main()
