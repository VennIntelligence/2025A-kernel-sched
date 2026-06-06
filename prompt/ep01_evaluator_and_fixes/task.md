# EP01: Build Evaluator & Fix Infrastructure

> Orchestration prompt — the executing agent should delegate sub-tasks to sub-agents and coordinate, not implement everything inline.

---

## Goal

Build a trustworthy evaluator/checker for the kernel scheduling competition (Problems 1/2/3), and fix existing infrastructure bugs that block validation. Until this is done, we cannot reliably judge whether any algorithm output is legal or better than baseline.

---

## Context

### What this competition is about

A neural-operator computation DAG must be scheduled on a multi-cache, multi-pipe NPU core. Three nested problems:

- **P1**: Find a topological order that minimizes peak cache residency (`maxV_stay`).
- **P2**: Assign physical cache offsets + insert spill/reload nodes, minimizing extra DDR traffic.
- **P3**: Optimize total pipelined execution time without significantly increasing extra traffic.

### Key files to read first

| file | what it tells you |
|------|-------------------|
| `docs/problem.md` | Complete problem specification (constraints, formulas, formats) |
| `src/ks_core/types.py` | Current data models |
| `src/ks_core/graph.py` | DAG loader (JSON/CSV) |
| `src/ks_core/io.py` | I/O utilities (has a known bug) |
| `src/ks_core/metrics.py` | Placeholder metrics — to be replaced by evaluator |
| `scripts/validate_schedule.py` | Current P1-only validator |
| `algorithms/baseline_gpt/` | Baseline outputs (schedule/memory/spill for all 6 cases × 3 problems) |
| `algorithms/baseline_gpt/metrics.csv` | Baseline benchmark numbers |

### Hardware constants (from problem statement)

```
Cache capacities: L1=4096, UB=1024, L0A=256, L0B=256, L0C=512
Pipes: MTE1, MTE2, MTE3, CUBE, VECTOR, FIXP
Cache nodes (ALLOC/FREE): Cycles=0
Spill pipes: SPILL_OUT→MTE3, SPILL_IN→MTE2
```

---

## Design Decisions (already agreed)

1. **Fix `get_project_root`** and align all path-dependent code with the fix.
2. **Create `src/ks_core/evaluator.py`** as a standalone module (do NOT merge into `metrics.py`).
3. **Keep schedule / memory / spill as separate data** — do NOT unify into a single `Solution` class. Use plain types: `list[int]` for schedule order, `dict[int, int]` for memory (BufId→Offset), `list[tuple[int, int]]` for spill entries (BufId, NewOffset).

---

## Task Breakdown

The executing agent should spawn sub-agents for independent tasks. Tasks within the same phase can run in parallel.

### Phase 0: Bug Fixes (parallel, all independent)

#### Task 0a: Fix `get_project_root` in `src/ks_core/io.py`

**Problem**: `get_project_root()` walks up from `src/ks_core/io.py` and hits `src/pyproject.toml` first, returning `src/` instead of the true project root.

**Fix**: The project root is the directory containing `src/` as a subdirectory. Change the detection logic — for example, require `(current / "src" / "ks_core").is_dir()` as the marker, or check for `(current / "data").is_dir()`. Choose whichever is simplest and least fragile.

**Verify**: After fixing, run:
```python
from ks_core.io import get_project_root, data_dir
assert (data_dir() / "json" / "Conv_Case0.json").exists()
```

#### Task 0b: Fix CSV loader bugs in `src/ks_core/graph.py`

Two bugs in `load_csv`:
1. **Line 80**: `bufs_raw.split(";")` should be `bufs_raw.split(",")` — CSV data uses comma-separated Bufs (e.g., `"5,3"`).
2. **Line 100**: `row["Src"]` / `row["Dst"]` should be `row["StartNodeId"]` / `row["EndNodeId"]` — match the actual CSV headers.

**Verify**: After fixing, load `Conv_Case0` via CSV and compare node/edge counts with JSON loader output. They must match exactly (2580 nodes, 3869 edges).

#### Task 0c: Fix `OpType` enum completeness in `src/ks_core/types.py`

Add missing Op values observed in the data: `COPY`, `ADD`, `SUB`, `MUL`, `MAX`, `EXP`, `REC`, `ROWMAX`, `ROWSUM`, `COMPACT`, `D2S`. Also add `FIXP` to `Pipe` enum.

Note: `Node.op` is typed as `str`, not `OpType`, so this is non-blocking. But the enum should be complete for anyone who wants to use it.

### Phase 1: I/O for P2/P3 Artifacts (parallel, all independent)

#### Task 1a: Add `read_memory_txt` and `write_memory_txt` to `src/ks_core/io.py`

Format: one `BufId:Offset` per line. Return `dict[int, int]`.

Reference file: `algorithms/baseline_gpt/Problem2/Conv_Case0_memory.txt`

#### Task 1b: Add `read_spill_txt` and `write_spill_txt` to `src/ks_core/io.py`

Format: one `BufId:NewOffset` per line. Return `list[tuple[int, int]]` (ordered — order matters for spill node id generation).

Reference file: `algorithms/baseline_gpt/Problem2/Conv_Case0_spill.txt`

Note: A BufId can appear multiple times in spill.txt (re-spill). The reader must preserve order and duplicates.

**Verify both**: Round-trip test — read a baseline file, write to temp, read back, assert equal.

### Phase 2: Evaluator Core — `src/ks_core/evaluator.py`

This is the critical deliverable. Build it incrementally as sub-functions:

#### Task 2a: `compute_max_vstay` — P1 Peak Residency

```python
def compute_max_vstay(
    order: list[int],
    nodes: dict[int, Node],
) -> dict[str, int]:
    """Scan schedule order, accumulate ALLOC(+Size) / FREE(-Size) per cache type.

    Returns:
        {"L1": max_L1, "UB": max_UB, "L0A": max_L0A, "L0B": max_L0B, "L0C": max_L0C}
    """
```

Also compute per-L0-type max concurrent buffer count (the constraint is: at most 1 buffer of each L0 type resident at any time).

**Verify**: Run on all 6 baseline P1 schedules, compare output against `metrics.csv` columns `max_L1, max_UB, max_L0A_count, max_L0B_count, max_L0C_count`.

#### Task 2b: `validate_memory` — P2 Address Feasibility

```python
def validate_memory(
    order: list[int],
    nodes: dict[int, Node],
    memory: dict[int, int],
    capacities: dict[str, int] | None = None,
) -> list[str]:
    """Check:
    1. Every buffer has an offset entry in memory.
    2. offset >= 0 and offset + size <= capacity for the buffer's cache type.
    3. No two same-cache-type buffers with overlapping schedule lifetimes
       have overlapping address intervals [offset, offset+size).

    Returns list of error strings (empty = valid).
    """
```

Default capacities: `{"L1": 4096, "UB": 1024, "L0A": 256, "L0B": 256, "L0C": 512}`.

"Schedule lifetime" of a buffer = from the position of its ALLOC node to the position of its FREE node in the schedule order. (For spilled buffers, lifetime is segmented — but that's handled in Task 2c.)

**Verify**: Run on all 6 baseline P2 memory files. Expect 0 errors.

#### Task 2c: `validate_spill` — P2/P3 Spill Legality

```python
def validate_spill(
    order: list[int],
    nodes: dict[int, Node],
    edges: list[Edge],
    spill_entries: list[tuple[int, int]],
    num_original_nodes: int,
) -> list[str]:
    """Check:
    1. Spill node id generation: spill k (1-indexed) creates SPILL_OUT=N+2(k-1), SPILL_IN=N+2(k-1)+1.
    2. Schedule contains all original + all spill node ids, exactly once.
    3. Spill dependency edges are respected in schedule order:
       ALLOC(buf) -> ... users before SPILL_OUT -> SPILL_OUT -> SPILL_IN -> users after SPILL_IN -> ... -> FREE(buf)
    4. Original DAG edges still respected.

    Returns list of error strings.
    """
```

**Verify**: Run on all 6 baseline P2 schedules+spills. Expect 0 errors.

#### Task 2d: `compute_extra` — P2 Extra DDR Traffic

```python
def compute_extra(
    spill_entries: list[tuple[int, int]],
    nodes: dict[int, Node],
) -> int:
    """Compute total extra data movement from spills.

    For each spill entry (buf_id, new_offset):
      - If buf_id's buffer is used by any COPY_IN node: cost = Size
      - Else: cost = 2 * Size

    Returns total extra.
    """
```

Need to precompute: for each buf_id, whether any operation node with Op=COPY_IN has that buf_id in its Bufs list.

**Verify**: Compare against baseline `metrics.csv` column `extra` for all 6 cases P2.

#### Task 2e: `compute_total_time` — P3 Pipelined Execution Time

```python
def compute_total_time(
    order: list[int],
    nodes: dict[int, Node],
    edges: list[Edge],
    memory: dict[int, int] | None = None,
    spill_entries: list[tuple[int, int]] | None = None,
    num_original_nodes: int | None = None,
) -> int:
    """Compute T = max_i E(v_i) with:

    For each node v_i in schedule order:
      S(v_i) >= 0
      S(v_i) >= E(u) for every predecessor u (original edges + spill edges + address-reuse edges)
      Same-pipe serialization: for consecutive nodes on the same pipe in schedule order,
        S(v_i) >= E(v_prev_on_same_pipe)
      E(v_i) = S(v_i) + Cycles(v_i)
      Cache nodes (ALLOC/FREE) have Cycles=0.

    Address-reuse edges: If buffer b's [offset, offset+size) overlaps with buffer a's interval,
    and ALLOC(b) comes after ALLOC(a) in schedule order, then add edge FREE(a) -> ALLOC(b).
    (Only for same cache type.)

    Spill nodes: SPILL_OUT has Pipe=MTE3, SPILL_IN has Pipe=MTE2.
    Spill cycles:
      If target buffer used by COPY_IN: SPILL_OUT cycles=0, SPILL_IN cycles=Size*2+150
      Else: SPILL_OUT cycles=Size*2+150, SPILL_IN cycles=Size*2+150

    Returns total execution time T.
    """
```

**Verify**: Compare against baseline `metrics.csv` column `time` for all 6 cases × P1/P2/P3. P1 time should match when memory=None and spill_entries=None.

### Phase 3: Integration

#### Task 3a: Wire evaluator into `scripts/validate_schedule.py`

Extend the existing validator to accept `--problem 2` or `--problem 3` with optional `--memory` and `--spill` paths. When provided, run the full P2/P3 checks in addition to P1 checks.

Keep backward compatibility: `--problem 1` (default) works as before but now also prints `maxV_stay` metrics.

#### Task 3b: Add a `scripts/eval_baseline.py` script

A one-shot script that:
1. Loads all 6 baseline cases × 3 problems from `algorithms/baseline_gpt/Problem{1,2,3}/`.
2. Runs the evaluator on each.
3. Prints a comparison table: our computed metrics vs. `metrics.csv` values.
4. Exits with error if any mismatch exceeds tolerance.

This is the acceptance test for the evaluator — if it reproduces baseline numbers, the evaluator is trustworthy.

#### Task 3c: Update `experiments/run_experiment.py`

After solving, also:
1. Save `memory.txt` and `spill.txt` when `problem_id >= 2` (requires the solve interface to return them — but for now, just add the I/O wiring; the actual algorithm can return empty).
2. Run `compute_max_vstay` (and `compute_extra` / `compute_total_time` when applicable) and save to `metrics.json`.

---

## Parallelism Guide for the Orchestrator Agent

```
Phase 0: [0a, 0b, 0c] — all parallel, no dependencies
Phase 1: [1a, 1b] — all parallel, no dependencies
Phase 2: [2a, 2b, 2c, 2d] — all parallel (each is an independent function)
         [2e] — can start in parallel but may want to reference 2a-2d patterns
Phase 3: [3a, 3b, 3c] — 3b depends on all of Phase 2; 3a and 3c can start after Phase 1+2
```

Spawn one sub-agent per task. Each sub-agent should:
1. Read the relevant source files and `docs/problem.md` sections.
2. Implement the change.
3. Write a minimal verification script in `tmp/` and run it.
4. Report back: what changed, what the verification output was.

The orchestrator should:
- Launch Phase 0 tasks in parallel.
- After Phase 0 completes, launch Phase 1 tasks in parallel.
- After Phase 1 completes, launch Phase 2 tasks in parallel.
- After Phase 2 completes, launch Phase 3 tasks.
- After Phase 3b (`eval_baseline.py`) passes, the episode is done.

---

## Acceptance Criteria

The episode is complete when `scripts/eval_baseline.py` runs successfully and reproduces baseline `metrics.csv` numbers for all 18 data points (6 cases × 3 problems) within tolerance:

- `max_L1`, `max_UB`, `max_L0A_count`, `max_L0B_count`, `max_L0C_count`: exact match
- `extra`: exact match
- `time`: exact match (deterministic computation, no tolerance needed)
- `spills` count: exact match
- All P2 memory validations pass (0 errors)
- All P2/P3 spill validations pass (0 errors)

---

## Coding Standards

- Follow `CLAUDE.md` global coding doctrine: senior-level, no over-design, no tutorial code.
- Follow `AGENTS.md` project conventions.
- All code in English; all communication in Chinese.
- No speculative abstractions. Each function does one thing.
- Prefer guard clauses and early returns.
- Do not add try/except unless there is a real recovery path.
- Temporary verification scripts go in `tmp/`, not in project source directories.
