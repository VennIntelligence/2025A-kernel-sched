# `agent_cost_order_search.py`

Research-only order-repair exploration for P2. It contains several
exploratory search modes rather than one uniform six-case algorithm; all
order generators are case-agnostic and use only the input DAG and buffer
metadata — official baseline schedules are loaded only in the final
reporting path, never as an input to a generator.

Not integrated into the default solver.

## Usage

```
uv run python scripts/agent_cost_order_search.py <mode> [options]
```

Modes: `inspect`, `proxy`, `probe`, `multistart`, `local_multistart`,
`hillclimb`, `targeted`, `spill_report`, `policy_probe`, `unlock_grid`,
`unlock_hill`, `unlock_targeted`, `final`.

Common options: `--case`, `--cases`, `--full`, `--seeds`, `--iters`,
`--seed`, `--rounds`, `--beam`.

## Reproducing the recorded runs

The recorded runs use the asymmetric traffic key but differ in proposal
family and budget — they are heterogeneous by design, not a single uniform
method:

```bash
# Conv0: seed-0 stochastic single-node hill search, 10,000 proposals
uv run python scripts/agent_cost_order_search.py unlock_hill \
  --cases Conv_Case0 --iters 10000 --seed 0

# Conv1: targeted spill-frontier beam, width 10 for two rounds
uv run python scripts/agent_cost_order_search.py unlock_targeted \
  --cases Conv_Case1 --rounds 2 --beam 10

# Smaller no-gain probes on FA0 and FA1
uv run python scripts/agent_cost_order_search.py unlock_hill \
  --cases FlashAttention_Case0 FlashAttention_Case1 --iters 2000 --seed 0

# Compare the saved orders; this command does not itself run those searches
uv run python scripts/agent_cost_order_search.py final
```

Expected additional improvements over the structural order are limited to:

- Conv_Case0: 66,828 → 65,532
- Conv_Case1: 72,734 → 70,940
- FA0/FA1: no observed gain under their 2,000-proposal probes
- MM0/MM1: repair search not run

The output directory does not persist a complete canonical artifact for
every repair row. Treat the Conv gains as exploratory mechanism evidence,
not as a uniform method, production default, or four-case negative result.

## Source of record

`results/autoresearch_v2/agent_cost_order/final_summary.json` is the
source-of-record output. See also `results/autoresearch_v2/RESEARCH_REPORT.md`
and `docs/research_summary.md` for the paper-facing narrative.
