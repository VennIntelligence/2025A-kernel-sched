# ruff: noqa: E402, I001
"""Audited paper-v2 evidence tables and figures.

Every numeric input is loaded from a machine-readable AutoResearch-v2 artifact.
The legacy E5 residency curves and legacy headline tables are intentionally not
read here.  Figures use the project-wide academic plotting API and are emitted
to both the executed-notebook output directory and the paper asset directory.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "paper"))

import harness as H  # noqa: E402
from ks_core.io import read_spill_txt  # noqa: E402
from ks_core.plotting import (
    CASE_LABELS,
    CASE_ORDER,
    METHOD_PALETTE,
    add_reference_line,
    make_figure,
    savefig_academic,
)  # noqa: E402

V2 = ROOT / "results" / "autoresearch_v2"
RESULTS = ROOT / "results" / "paper"
OUTPUT = ROOT / "output" / "02_paper_figures"
PAPER_FIGURES = ROOT / "paper" / "assets" / "figures"
PAPER_TABLES = ROOT / "paper" / "assets" / "tables"

PUBLIC_CSV = RESULTS / "v2_public_p2_p3.csv"
METHOD_CSV = RESULTS / "v2_conv0_method_path.csv"
COST_CSV = RESULTS / "v2_conv0_cost_identity.csv"
EXACT_CSV = RESULTS / "v2_exact_evidence_scope.csv"
EXACT_SCOPE_JSON = RESULTS / "v2_exact_scope_summary.json"
CAPACITY_CSV = RESULTS / "v2_capacity_boundary.csv"
SYNTH_CSV = RESULTS / "v2_synthetic_boundary.csv"
ATTRIBUTION_CSV = RESULTS / "v2_component_attribution.csv"
ALL_COST_CSV = RESULTS / "v2_all_cases_cost_decomposition.csv"
DECOUPLING_CSV = RESULTS / "v2_p2_p3_decoupling.csv"
MANIFEST_CSV = RESULTS / "v2_evidence_manifest.csv"


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _case_rows(rows: list[dict]) -> dict[str, dict]:
    return {row["case"]: row for row in rows}


def _assert_canonical(rows: list[dict], label: str) -> None:
    assert [row["case"] for row in rows] == CASE_ORDER, label
    assert all(row["valid"] and row["violations"] == 0 for row in rows), label


def _spill_components(spill_path: Path, case: str = "Conv_Case0") -> dict[str, int]:
    inst = H.load_instance(case, 2)
    split = H.extra_split(read_spill_txt(spill_path), inst)
    assert split["dirty_bytes"] % 2 == 0
    backed = int(split["clean_bytes"])
    generated = int(split["dirty_bytes"] // 2)
    extra = backed + 2 * generated
    assert extra == split["extra"]
    return {
        "backed_volume": backed,
        "generated_volume": generated,
        "volume": backed + generated,
        "generated_surcharge": generated,
        "extra": extra,
        "spills": int(split["spills"]),
    }


def _split_fields(row: dict, prefix: str = "") -> dict[str, int]:
    backed = int(row[f"{prefix}clean_bytes"])
    generated_contribution = int(row[f"{prefix}dirty_bytes"])
    assert generated_contribution % 2 == 0
    generated = generated_contribution // 2
    extra = int(row[f"{prefix}extra"])
    assert extra == backed + 2 * generated
    return {
        "backed_volume": backed,
        "generated_volume": generated,
        "volume": backed + generated,
        "generated_surcharge": generated,
        "extra": extra,
    }


def prepare_data() -> dict[str, pd.DataFrame]:
    """Derive all v2 tables and enforce the paper claim ledger contract."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PAPER_FIGURES.mkdir(parents=True, exist_ok=True)
    PAPER_TABLES.mkdir(parents=True, exist_ok=True)

    p2_rows = _read_json(V2 / "round10_final_p2.json")
    p3_rows = _read_json(V2 / "round6_formal_p3.json")
    _assert_canonical(p2_rows, "P2")
    _assert_canonical(p3_rows, "P3")
    p2 = _case_rows(p2_rows)
    p3 = _case_rows(p3_rows)
    audited_p2_rows = _read_json(V2 / "round11_audited_p2.json")
    _assert_canonical(audited_p2_rows, "audited P2")
    audited_p2 = _case_rows(audited_p2_rows)
    assert all(
        audited_p2[case]["extra"] == p2[case]["extra"]
        and audited_p2[case]["time"] == p2[case]["time"]
        for case in CASE_ORDER
    )

    public = []
    for case in CASE_ORDER:
        r2, r3 = p2[case], p3[case]
        public.append(
            {
                "case": case,
                "label": CASE_LABELS[case],
                "p2_scalable_extra": int(r2["extra"]),
                "p2_official_extra": int(r2["official_extra"]),
                "p2_ratio": r2["extra"] / r2["official_extra"],
                "p2_reduction_pct": 100
                * (r2["official_extra"] - r2["extra"])
                / r2["official_extra"],
                "p2_result": "WIN" if r2["extra"] < r2["official_extra"] else "TIE",
                "p3_scalable_time": int(r3["time"]),
                "p3_official_time": int(r3["official_time"]),
                "p3_ratio": r3["time"] / r3["official_time"],
                "p3_delta_pct": 100 * (r3["time"] - r3["official_time"]) / r3["official_time"],
                "p3_result": "WIN" if r3["time"] < r3["official_time"] else "LOSS",
                "valid": bool(r2["valid"] and r3["valid"]),
                "violations": int(r2["violations"] + r3["violations"]),
            }
        )
    public_df = pd.DataFrame(public)
    assert list(public_df["p2_result"]).count("WIN") == 5
    assert list(public_df["p2_result"]).count("TIE") == 1
    assert list(public_df["p3_result"]).count("WIN") == 5
    assert list(public_df["p3_result"]).count("LOSS") == 1
    public_df.to_csv(PUBLIC_CSV, index=False)

    repair_rows = _read_json(V2 / "agent_cost_order" / "final_summary.json")["rows"]
    predecessor = _case_rows(repair_rows)
    ablation = _read_json(V2 / "round7_public_ablation.json")
    ablation_by_case = {
        case: {row["scheme"]: row for row in ablation if row["case"] == case} for case in CASE_ORDER
    }
    required_schemes = {"iter038", "best_fit_only", "unlock_only", "full"}
    assert all(required_schemes <= set(rows) for rows in ablation_by_case.values())

    attribution_rows = []
    all_cost_rows = []
    for case in CASE_ORDER:
        rows = ablation_by_case[case]
        h0_reference = int(rows["iter038"]["extra"])
        best_fit = int(rows["best_fit_only"]["extra"])
        frontier = int(rows["unlock_only"]["extra"])
        full = int(rows["full"]["extra"])
        actual_predecessor = int(predecessor[case]["old_iter038_extra"])
        additive_prediction = best_fit + frontier - h0_reference
        attribution_rows.append(
            {
                "case": case,
                "label": CASE_LABELS[case],
                "production_predecessor_extra": actual_predecessor,
                "h0_reference_extra": h0_reference,
                "best_fit_only_extra": best_fit,
                "frontier_only_extra": frontier,
                "selected_full_extra": full,
                "production_delta": full - actual_predecessor,
                "h0_reference_ratio": 1.0,
                "best_fit_only_ratio": best_fit / h0_reference,
                "frontier_only_ratio": frontier / h0_reference,
                "selected_full_ratio": full / h0_reference,
                "naive_additive_prediction": additive_prediction,
                "deviation_from_additive": additive_prediction - full,
            }
        )

        production = audited_p2[case]
        split = {
            "backed_volume": int(production["backed_volume"]),
            "generated_volume": int(production["generated_volume"]),
            "volume": int(production["spill_volume"]),
            "generated_surcharge": int(production["generated_volume"]),
            "extra": int(production["extra"]),
        }
        assert split["volume"] == split["backed_volume"] + split["generated_volume"]
        assert split["extra"] == split["volume"] + split["generated_surcharge"]
        official_split = _spill_components(
            ROOT / "results" / "exp001_baseline01" / "spills" / f"P2_{case}_spill.txt",
            case,
        )
        assert official_split["extra"] == int(p2[case]["official_extra"])
        volume_reduction = official_split["volume"] - split["volume"]
        generated_reduction = official_split["generated_volume"] - split["generated_volume"]
        extra_reduction = official_split["extra"] - split["extra"]
        assert extra_reduction == volume_reduction + generated_reduction
        all_cost_rows.append(
            {
                "case": case,
                "label": CASE_LABELS[case],
                "official_backed_volume": official_split["backed_volume"],
                "official_generated_volume": official_split["generated_volume"],
                "official_volume": official_split["volume"],
                "official_extra": official_split["extra"],
                "scalable_backed_volume": split["backed_volume"],
                "scalable_generated_volume": split["generated_volume"],
                "scalable_volume": split["volume"],
                "scalable_extra": split["extra"],
                "volume_reduction": volume_reduction,
                "generated_reduction": generated_reduction,
                "extra_reduction": extra_reduction,
            }
        )

    attribution_df = pd.DataFrame(attribution_rows)
    assert tuple(
        np.sign(attribution_df["production_delta"]).value_counts().sort_index().to_numpy()
    ) == (3, 2, 1)
    assert (
        int(
            attribution_df.loc[
                attribution_df["case"] == "Conv_Case0", "deviation_from_additive"
            ].iloc[0]
        )
        == 18484
    )
    attribution_df.to_csv(ATTRIBUTION_CSV, index=False)

    all_cost_df = pd.DataFrame(all_cost_rows)
    assert np.array_equal(
        all_cost_df["scalable_extra"].to_numpy(),
        public_df["p2_scalable_extra"].to_numpy(),
    )
    assert np.array_equal(
        all_cost_df["extra_reduction"].to_numpy(),
        (all_cost_df["volume_reduction"] + all_cost_df["generated_reduction"]).to_numpy(),
    )
    all_cost_df.to_csv(ALL_COST_CSV, index=False)

    decoupling_rows = []
    for case in CASE_ORDER:
        p2_row, p3_row = p2[case], p3[case]
        traffic_delta = int(p3_row["extra"] - p2_row["extra"])
        latency_delta = int(p3_row["time"] - p2_row["time"])
        assert traffic_delta > 0 and latency_delta < 0
        decoupling_rows.append(
            {
                "case": case,
                "label": CASE_LABELS[case],
                "p2_extra": int(p2_row["extra"]),
                "p3_extra": int(p3_row["extra"]),
                "traffic_delta_bytes": traffic_delta,
                "traffic_delta_pct": 100 * traffic_delta / p2_row["extra"],
                "p2_time": int(p2_row["time"]),
                "p3_time": int(p3_row["time"]),
                "latency_delta_cycles": latency_delta,
                "latency_delta_pct": 100 * latency_delta / p2_row["time"],
                "interpretation": "P3 uses more traffic and less time",
            }
        )
    decoupling_df = pd.DataFrame(decoupling_rows)
    conv1_tradeoff = decoupling_df[decoupling_df["case"] == "Conv_Case1"].iloc[0]
    assert int(conv1_tradeoff["traffic_delta_bytes"]) == 8
    assert int(conv1_tradeoff["latency_delta_cycles"]) == -35985
    decoupling_df.to_csv(DECOUPLING_CSV, index=False)

    conv0_ablation = {r["scheme"]: r for r in ablation if r["case"] == "Conv_Case0"}
    repair = _case_rows(repair_rows)["Conv_Case0"]
    exact = _read_json(V2 / "agent_direct" / "P2_Conv_Case0_unlock_frontier_exact.json")
    exact_p1 = _read_json(V2 / "agent_direct" / "P2_Conv_Case0_p1_exact.json")
    exact_fa0 = _read_json(V2 / "agent_direct" / "P2_FlashAttention_Case0_id_raw_exact.json")
    exact_fa1 = _read_json(V2 / "agent_direct" / "P2_FlashAttention_Case1_capfit_id_exact.json")
    exact_mm0 = _read_json(V2 / "agent_direct" / "P2_Matmul_Case0_capfit_id_exact.json")
    assert exact["valid"] and exact["solver_status"] == "OPTIMAL"
    assert exact["packing_status"] == "OPTIMAL"
    assert exact["extra"] == exact["lower_bound_extra"] and exact["optimality_gap"] == 0
    for record, case, stem in (
        (exact_p1, "Conv_Case0", "P2_Conv_Case0_p1_exact"),
        (exact_fa0, "FlashAttention_Case0", "P2_FlashAttention_Case0_id_raw_exact"),
        (exact_fa1, "FlashAttention_Case1", "P2_FlashAttention_Case1_capfit_id_exact"),
        (exact_mm0, "Matmul_Case0", "P2_Matmul_Case0_capfit_id_exact"),
    ):
        assert record["valid"] and record["packing_status"] in {"OPTIMAL", "GREEDY_VALID"}
        assert _spill_components(V2 / "agent_direct" / f"{stem}_spill.txt", case)["extra"] == int(
            record["extra"]
        )
    assert exact_p1["solver_status"] == "OPTIMAL"
    assert exact_fa0["solver_status"] == "OPTIMAL"
    assert exact_fa1["solver_status"] == "FEASIBLE"
    assert exact_mm0["solver_status"] == "FEASIBLE"

    official_components = _spill_components(
        ROOT / "results" / "exp001_baseline01" / "spills" / "P2_Conv_Case0_spill.txt"
    )
    method_df = pd.DataFrame(
        [
            {
                "stage": "legacy",
                "label": "Legacy iter038",
                "extra": int(conv0_ablation["iter038"]["extra"]),
                "spills": int(conv0_ablation["iter038"]["spills"]),
                "scope": "P2 scalable predecessor",
            },
            {
                "stage": "scalable",
                "label": "Scalable v2",
                "extra": int(p2["Conv_Case0"]["extra"]),
                "spills": int(p2["Conv_Case0"]["spills"]),
                "scope": "P2 production",
            },
            {
                "stage": "repair",
                "label": "Cost-aware repair",
                "extra": int(repair["cost_search_extra"]),
                "spills": int(repair["cost_search_spills"]),
                "scope": "Conv0-only 10k stochastic hill search",
            },
            {
                "stage": "exact",
                "label": "Fixed-order exact",
                "extra": int(exact["extra"]),
                "spills": int(exact["spills"]),
                "scope": "fixed-order traffic oracle (E only)",
            },
            {
                "stage": "official",
                "label": "Official",
                "extra": int(p2["Conv_Case0"]["official_extra"]),
                "spills": official_components["spills"],
                "scope": "P2 official artifact",
            },
        ]
    )
    method_df.to_csv(METHOD_CSV, index=False)

    components = {
        "legacy": _split_fields(conv0_ablation["iter038"]),
        "scalable": _split_fields(conv0_ablation["full"]),
        "repair": _split_fields(repair, prefix="cost_search_"),
        "exact": _spill_components(
            V2 / "agent_direct" / "P2_Conv_Case0_unlock_frontier_exact_spill.txt"
        ),
        "official": official_components,
    }
    cost_rows = []
    label_by_stage = dict(zip(method_df["stage"], method_df["label"]))
    for stage in ("legacy", "scalable", "repair", "exact", "official"):
        row = {"stage": stage, "label": label_by_stage[stage], **components[stage]}
        assert row["extra"] == row["volume"] + row["generated_surcharge"]
        cost_rows.append(row)
    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(COST_CSV, index=False)

    node_count = {row["case"]: int(row["schedule_len"] - 2 * row["spills"]) for row in p2_rows}
    # Machine artifacts establish fixed-order traffic optimality only: the gap
    # model minimizes E, not the benchmark's spill-count/time tie-breaks.
    # Remaining rows are provisional run-log metadata and are visually
    # separated from machine-checkable artifacts.
    exact_scope_records = [
        {
            "case": "FlashAttention_Case0",
            "label": "FA 0",
            "order": "id_raw",
            "original_nodes": node_count["FlashAttention_Case0"],
            "status": exact_fa0["solver_status"],
            "objective": int(exact_fa0["extra"]),
            "lower_bound": int(exact_fa0["lower_bound_extra"]),
            "gap": int(exact_fa0["optimality_gap"]),
            "wall_seconds": float(exact_fa0["wall_seconds"]),
            "packing_status": exact_fa0["packing_status"],
            "validity": "canonical-valid",
            "record_kind": "machine_traffic_certificate",
            "source": (
                "results/autoresearch_v2/agent_direct/P2_FlashAttention_Case0_id_raw_exact.json"
            ),
        },
        {
            "case": "Conv_Case0",
            "label": "Conv 0",
            "order": "unlock_frontier",
            "original_nodes": node_count["Conv_Case0"],
            "status": "OPTIMAL",
            "objective": int(exact["extra"]),
            "lower_bound": int(exact["lower_bound_extra"]),
            "gap": 0,
            "wall_seconds": float(exact["wall_seconds"]),
            "packing_status": exact["packing_status"],
            "validity": "canonical-valid",
            "record_kind": "machine_traffic_certificate",
            "source": (
                "results/autoresearch_v2/agent_direct/P2_Conv_Case0_unlock_frontier_exact.json"
            ),
        },
        {
            "case": "Conv_Case0",
            "label": "Conv 0",
            "order": "p1",
            "original_nodes": node_count["Conv_Case0"],
            "status": exact_p1["solver_status"],
            "objective": int(exact_p1["extra"]),
            "lower_bound": int(exact_p1["lower_bound_extra"]),
            "gap": int(exact_p1["optimality_gap"]),
            "wall_seconds": float(exact_p1["wall_seconds"]),
            "packing_status": exact_p1["packing_status"],
            "validity": "canonical-valid",
            "record_kind": "machine_traffic_certificate",
            "source": "results/autoresearch_v2/agent_direct/P2_Conv_Case0_p1_exact.json",
        },
        {
            "case": "Matmul_Case0",
            "label": "Matmul 0",
            "order": "capfit_id",
            "original_nodes": node_count["Matmul_Case0"],
            "status": exact_mm0["solver_status"],
            "objective": int(exact_mm0["extra"]),
            "lower_bound": int(exact_mm0["lower_bound_extra"]),
            "gap": int(exact_mm0["optimality_gap"]),
            "wall_seconds": float(exact_mm0["wall_seconds"]),
            "packing_status": exact_mm0["packing_status"],
            "validity": "canonical-valid",
            "record_kind": "machine_feasible_artifact",
            "source": "results/autoresearch_v2/agent_direct/P2_Matmul_Case0_capfit_id_exact.json",
        },
        {
            "case": "FlashAttention_Case1",
            "label": "FA 1",
            "order": "capfit_id",
            "original_nodes": node_count["FlashAttention_Case1"],
            "status": exact_fa1["solver_status"],
            "objective": int(exact_fa1["extra"]),
            "lower_bound": int(exact_fa1["lower_bound_extra"]),
            "gap": int(exact_fa1["optimality_gap"]),
            "wall_seconds": float(exact_fa1["wall_seconds"]),
            "packing_status": exact_fa1["packing_status"],
            "validity": "canonical-valid",
            "record_kind": "machine_feasible_artifact",
            "source": (
                "results/autoresearch_v2/agent_direct/P2_FlashAttention_Case1_capfit_id_exact.json"
            ),
        },
        {
            "case": "Matmul_Case1",
            "label": "Matmul 1",
            "order": "run-log only",
            "original_nodes": node_count["Matmul_Case1"],
            "status": "FALLBACK_NOT_RUN",
            "objective": None,
            "lower_bound": None,
            "gap": None,
            "wall_seconds": None,
            "packing_status": None,
            "validity": "provisional run-log only",
            "record_kind": "audited_status_metadata",
            "source": "results/autoresearch_v2/CLAIM_LEDGER.md",
        },
        {
            "case": "Conv_Case1",
            "label": "Conv 1",
            "order": "run-log only",
            "original_nodes": node_count["Conv_Case1"],
            "status": "FALLBACK_TIMEOUT",
            "objective": None,
            "lower_bound": None,
            "gap": None,
            "wall_seconds": None,
            "packing_status": None,
            "validity": "provisional run-log only",
            "record_kind": "audited_status_metadata",
            "source": (
                "results/autoresearch_v2/agent_direct/REPORT.md + "
                "results/autoresearch_v2/CLAIM_LEDGER.md"
            ),
        },
    ]
    EXACT_SCOPE_JSON.write_text(
        json.dumps(
            {
                "description": (
                    "Discrete fixed-order traffic evidence; not a scaling experiment or "
                    "full benchmark-optimality claim. Conv0 unlock_frontier, Conv0 p1, and "
                    "FA0 are machine-checkable traffic-optimal certificates; MM0 is a "
                    "machine-checkable feasible artifact with a 4864-byte gap; FA1 is a "
                    "machine-checkable feasible artifact with a 576-byte gap; remaining "
                    "rows are provisional run-log metadata."
                ),
                "records": exact_scope_records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    exact_df = pd.DataFrame(exact_scope_records)
    assert exact_df.loc[exact_df["case"] == "FlashAttention_Case1", "gap"].iloc[0] == 576
    exact_df.to_csv(EXACT_CSV, index=False)

    capacity_df = pd.DataFrame(_read_json(V2 / "round8_capacity_sweep.json"))
    capacity_df.to_csv(CAPACITY_CSV, index=False)

    synth_summary = {r["regime"]: r for r in _read_json(V2 / "round9_synthetic_summary.json")}
    synthetic_df = pd.DataFrame(
        [
            {
                "comparison": "Capacity-bound\nvs cost-blind\nordering",
                "wins": synth_summary["capacity_bound"]["wins"],
                "ties": synth_summary["capacity_bound"]["ties"],
                "losses": synth_summary["capacity_bound"]["losses"],
            },
            {
                "comparison": "Order-reachable\nvs cost-blind\nordering",
                "wins": synth_summary["order_reachable"]["wins"],
                "ties": synth_summary["order_reachable"]["ties"],
                "losses": synth_summary["order_reachable"]["losses"],
            },
            {
                "comparison": "All synthetic\nvs iter038",
                "wins": synth_summary["all"]["improved_vs_iter038"],
                "ties": synth_summary["all"]["tied_vs_iter038"],
                "losses": synth_summary["all"]["regressed_vs_iter038"],
            },
        ]
    )
    assert tuple(synthetic_df.iloc[2][["wins", "ties", "losses"]]) == (0, 36, 0)
    synthetic_df.to_csv(SYNTH_CSV, index=False)

    _write_tables(
        public_df,
        method_df,
        cost_df,
        exact_df,
        capacity_df,
        synthetic_df,
        attribution_df,
        all_cost_df,
        decoupling_df,
    )
    manifest = pd.DataFrame(
        [
            {
                "artifact": PUBLIC_CSV.name,
                "source": "round10_final_p2.json + round6_formal_p3.json",
                "claim": "public P2/P3",
            },
            {
                "artifact": METHOD_CSV.name,
                "source": "round7 + round10 + repair final + exact JSON",
                "claim": "Conv0 method path",
            },
            {
                "artifact": COST_CSV.name,
                "source": "validated spill artifacts and split fields",
                "claim": "E=V+D identity",
            },
            {
                "artifact": EXACT_CSV.name,
                "source": EXACT_SCOPE_JSON.name,
                "claim": "fixed-order traffic certificates and provisional scope (not scaling)",
            },
            {
                "artifact": CAPACITY_CSV.name,
                "source": "round8_capacity_sweep.json",
                "claim": "controlled H=0 capacity boundary",
            },
            {
                "artifact": SYNTH_CSV.name,
                "source": "round9_synthetic_summary.json",
                "claim": "internal non-canonical synthetic non-regression",
            },
            {
                "artifact": ATTRIBUTION_CSV.name,
                "source": "round7_public_ablation.json + agent_cost_order/final_summary.json",
                "claim": "six-case selected H=0 configurations (non-factorial)",
            },
            {
                "artifact": ALL_COST_CSV.name,
                "source": "round11_audited_p2.json + official P2 spill artifacts",
                "claim": "official vs production Scalable v2 E=V+D accounting",
            },
            {
                "artifact": DECOUPLING_CSV.name,
                "source": "round10_final_p2.json + round6_formal_p3.json",
                "claim": "within-portfolio P2/P3 artifact tradeoff",
            },
        ]
    )
    manifest.to_csv(MANIFEST_CSV, index=False)
    return {
        "public": public_df,
        "method": method_df,
        "cost": cost_df,
        "exact": exact_df,
        "capacity": capacity_df,
        "synthetic": synthetic_df,
        "attribution": attribution_df,
        "all_cost": all_cost_df,
        "decoupling": decoupling_df,
    }


def _write_tex(df: pd.DataFrame, name: str, column_format: str | None = None) -> None:
    text = df.to_latex(index=False, escape=False, column_format=column_format)
    (PAPER_TABLES / name).write_text(text, encoding="utf-8")


def _write_tables(
    public,
    method,
    cost,
    exact_scope,
    capacity,
    synthetic,
    attribution,
    all_cost,
    decoupling,
) -> None:
    pub = public[
        [
            "label",
            "p2_scalable_extra",
            "p2_official_extra",
            "p2_result",
            "p3_scalable_time",
            "p3_official_time",
            "p3_result",
        ]
    ].rename(
        columns={
            "label": "Case",
            "p2_scalable_extra": "Scalable P2",
            "p2_official_extra": "Official P2",
            "p2_result": "P2",
            "p3_scalable_time": "Scalable P3",
            "p3_official_time": "Official P3",
            "p3_result": "P3",
        }
    )
    _write_tex(pub, "v2_public_p2_p3.tex", "lrrrrrr")

    path = method[["label", "extra", "spills", "scope"]].rename(
        columns={
            "label": "Method",
            "extra": "P2 extra",
            "spills": "Spills",
            "scope": "Scope",
        }
    )
    _write_tex(path, "v2_conv0_method_path.tex", "lrrl")

    ident = cost[
        ["label", "backed_volume", "generated_volume", "volume", "generated_surcharge", "extra"]
    ].rename(
        columns={
            "label": "Method",
            "backed_volume": "$C$",
            "generated_volume": "$D$",
            "volume": "$V=C+D$",
            "generated_surcharge": "Surcharge $D$",
            "extra": "$E=V+D$",
        }
    )
    _write_tex(ident, "v2_conv0_cost_identity.tex", "lrrrrr")

    cert = exact_scope[exact_scope["record_kind"] != "audited_status_metadata"][
        [
            "label",
            "order",
            "objective",
            "lower_bound",
            "gap",
            "status",
            "packing_status",
            "wall_seconds",
            "validity",
        ]
    ].copy()
    cert["Case/order"] = cert["label"] + " / " + cert["order"]
    for column in ("objective", "lower_bound", "gap"):
        cert[column] = cert[column].astype(int)
    cert["wall_seconds"] = cert["wall_seconds"].map(lambda value: f"{value:.2f}")
    cert = cert[
        [
            "Case/order",
            "objective",
            "lower_bound",
            "gap",
            "status",
            "packing_status",
            "wall_seconds",
            "validity",
        ]
    ].rename(
        columns={
            "objective": "Traffic $E$",
            "lower_bound": "Lower bound",
            "gap": "Traffic gap",
            "status": "Gap solver",
            "packing_status": "Packing",
            "wall_seconds": "Wall [s]",
            "validity": "Validity",
        }
    )
    _write_tex(cert, "v2_exact_certificate.tex", "lrrrllll")

    cap_feasible = capacity[capacity["status"] == "feasible"]
    boundary = pd.DataFrame(
        [
            {
                "Evidence": "Conv0 controlled H=0 sweep",
                "Result": "selected config. 7W/0L vs cost-blind ordering",
            },
            {"Evidence": "Pinned-set boundary", "Result": "2048 and 2560 bytes infeasible"},
            {
                "Evidence": "Internal synthetic vs cost-blind ordering",
                "Result": "14W / 22T / 0L; not canonical-validated",
            },
            {
                "Evidence": "Internal synthetic vs iter038",
                "Result": "0W / 36T / 0L; not canonical-validated",
            },
        ]
    )
    assert len(cap_feasible) == 7
    _write_tex(boundary, "v2_robustness_boundary.tex", "ll")

    components = attribution[
        [
            "label",
            "production_predecessor_extra",
            "h0_reference_extra",
            "best_fit_only_extra",
            "frontier_only_extra",
            "selected_full_extra",
            "production_delta",
            "naive_additive_prediction",
            "deviation_from_additive",
        ]
    ].rename(
        columns={
            "label": "Case",
            "production_predecessor_extra": "Actual predecessor",
            "h0_reference_extra": "$H=0$ reference",
            "best_fit_only_extra": "Best-fit only",
            "frontier_only_extra": "Frontier only",
            "selected_full_extra": "Selected full config.",
            "production_delta": "$\\Delta$ vs predecessor",
            "naive_additive_prediction": "Naive additive",
            "deviation_from_additive": "Deviation",
        }
    )
    _write_tex(components, "v2_component_attribution.tex", "lrrrrrrrr")

    all_case_identity = all_cost[
        [
            "label",
            "official_volume",
            "official_generated_volume",
            "official_extra",
            "scalable_volume",
            "scalable_generated_volume",
            "scalable_extra",
            "volume_reduction",
            "generated_reduction",
            "extra_reduction",
        ]
    ].rename(
        columns={
            "label": "Case",
            "official_volume": "Official $V$",
            "official_generated_volume": "Official $D$",
            "official_extra": "Official $E$",
            "scalable_volume": "Scalable $V$",
            "scalable_generated_volume": "Scalable $D$",
            "scalable_extra": "Scalable $E$",
            "volume_reduction": "$\\Delta V$",
            "generated_reduction": "$\\Delta D$",
            "extra_reduction": "$\\Delta E$",
        }
    )
    _write_tex(all_case_identity, "v2_all_cases_cost_decomposition.tex", "lrrrrrrrrr")

    deltas = decoupling[
        [
            "label",
            "traffic_delta_bytes",
            "traffic_delta_pct",
            "latency_delta_cycles",
            "latency_delta_pct",
        ]
    ].copy()
    deltas["traffic_delta_pct"] = deltas["traffic_delta_pct"].map(lambda value: f"{value:+.2f}")
    deltas["latency_delta_pct"] = deltas["latency_delta_pct"].map(lambda value: f"{value:+.2f}")
    deltas = deltas.rename(
        columns={
            "label": "Case",
            "traffic_delta_bytes": "$\\Delta$traffic [B]",
            "traffic_delta_pct": "$\\Delta$traffic [\\%]",
            "latency_delta_cycles": "$\\Delta$latency [cyc]",
            "latency_delta_pct": "$\\Delta$latency [\\%]",
        }
    )
    _write_tex(deltas, "v2_p2_p3_decoupling.tex", "lrrrr")


def _emit(render, stem: str):
    fig = render()
    png = OUTPUT / f"{stem}.png"
    savefig_academic(fig, png)
    shutil.copy2(png, PAPER_FIGURES / png.name)
    pdf_fig = render()
    savefig_academic(pdf_fig, PAPER_FIGURES / f"{stem}.pdf")
    return fig


def figure_public_p2_p3():
    df = pd.read_csv(PUBLIC_CSV)

    def render():
        fig, axes = make_figure("double_col", ncols=2, height=3.25)
        x = np.arange(len(df))
        specs = [
            ("p2_ratio", "P2 extra traffic (lower is better)", METHOD_PALETTE["primary"], "o"),
            ("p3_ratio", "P3 latency (lower is better)", METHOD_PALETTE["accent_3"], "s"),
        ]
        for ax, (column, title, color, marker) in zip(axes, specs):
            values = 100 * (df[column].to_numpy() - 1)
            ax.vlines(x, 0, values, color=color, linewidth=1.4, zorder=2)
            ax.scatter(x, values, color=color, marker=marker, zorder=3)
            add_reference_line(ax, 0.0, "Official parity")
            ax.set_title(title)
            ax.set_ylabel("Relative change vs official [%]")
            ax.set_xticks(x, df["label"])
            ax.grid(axis="y", alpha=0.3, linewidth=0.5)
            pad = max(0.35, (values.max() - values.min()) * 0.025)
            ax.set_ylim(values.min() - 3 * pad, max(0, values.max()) + 4 * pad)
            for xi, value in zip(x, values):
                offset = pad if value >= 0 else -pad
                ax.text(
                    xi,
                    value + offset,
                    f"{value:+.1f}%",
                    ha="center",
                    va="bottom" if value >= 0 else "top",
                    fontsize=7,
                )
        handles = [
            Line2D([0], [0], color=METHOD_PALETTE["primary"], marker="o", label="Scalable v2 (P2)"),
            Line2D(
                [0], [0], color=METHOD_PALETTE["accent_3"], marker="s", label="Scalable v2 (P3)"
            ),
            Line2D([0], [0], color="#666666", linestyle="--", label="Official parity"),
        ]
        fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=3)
        return fig

    return _emit(render, "public_p2_p3_vs_official")


def figure_conv0_method_path():
    df = pd.read_csv(METHOD_CSV)
    plotted = df[df["stage"] != "official"].copy()
    official = int(df.loc[df["stage"] == "official", "extra"].iloc[0])

    def render():
        fig, ax = make_figure("one_half_col", height=3.25)
        x = np.arange(len(plotted))
        colors = [
            METHOD_PALETTE["neutral"],
            METHOD_PALETTE["primary"],
            METHOD_PALETTE["accent_2"],
            METHOD_PALETTE["secondary"],
        ]
        vals = plotted["extra"].to_numpy() / 1000
        bars = ax.bar(x, vals, color=colors, edgecolor="white", linewidth=0.6, zorder=2)
        add_reference_line(
            ax, official / 1000, f"Official P2: {official:,} B", color=METHOD_PALETTE["accent_1"]
        )
        ax.set_xticks(x, ["Legacy", "Scalable v2", "Cost repair", "Fixed-order\nexact"])
        ax.set_ylabel("P2 extra traffic [KB]")
        ax.set_title("Conv 0: method decomposition")
        ax.set_ylim(0, max(vals) * 1.18)
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)
        for bar, raw in zip(bars, plotted["extra"]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.2,
                f"{int(raw):,}",
                ha="center",
                va="bottom",
                fontsize=7,
            )
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=1)
        return fig

    return _emit(render, "conv0_method_decomposition")


def figure_cost_identity():
    df = pd.read_csv(COST_CSV)

    def render():
        fig, ax = make_figure("double_col", height=3.55)
        x = np.arange(len(df))
        c = df["backed_volume"].to_numpy() / 1000
        d = df["generated_volume"].to_numpy() / 1000
        s = df["generated_surcharge"].to_numpy() / 1000
        ax.bar(
            x,
            c,
            color=METHOD_PALETTE["primary"],
            edgecolor="white",
            linewidth=0.6,
            label=r"Backed spill volume $C$",
        )
        ax.bar(
            x,
            d,
            bottom=c,
            color=METHOD_PALETTE["accent_3"],
            edgecolor="white",
            linewidth=0.6,
            label=r"Generated spill volume $D$",
        )
        ax.bar(
            x,
            s,
            bottom=c + d,
            color=METHOD_PALETTE["accent_1"],
            edgecolor="white",
            linewidth=0.6,
            label=r"Generated surcharge $D$",
        )
        ax.set_xticks(x, ["Legacy", "Scalable v2", "Cost repair", "Fixed-order\nexact", "Official"])
        ax.set_ylabel("P2 extra traffic [KB]")
        ax.set_title(r"Conv 0 accounting: $E=C+2D=(C+D)+D=V+D$")
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)
        for xi, total in zip(x, df["extra"]):
            ax.text(xi, total / 1000 + 1.1, f"{int(total):,}", ha="center", va="bottom", fontsize=7)
        ax.set_ylim(0, df["extra"].max() / 1000 * 1.2)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3)
        return fig

    return _emit(render, "spill_cost_identity")


def figure_exact_certificate_scope():
    df = pd.read_csv(EXACT_CSV)

    def render():
        fig, axes = make_figure("double_col", ncols=2, height=3.7)
        ax = axes[0]
        certificates = df[df["record_kind"] == "machine_traffic_certificate"].copy()
        y = np.arange(len(certificates))
        lower = certificates["lower_bound"].to_numpy() / 1000
        objective = certificates["objective"].to_numpy() / 1000
        ax.scatter(
            lower,
            y - 0.07,
            color=METHOD_PALETTE["neutral"],
            marker="o",
            label="Traffic lower bound",
            zorder=3,
        )
        ax.scatter(
            objective,
            y + 0.07,
            color=METHOD_PALETTE["secondary"],
            marker="X",
            label="Packed traffic objective",
            zorder=4,
        )
        for yi, (_, row) in zip(y, certificates.iterrows()):
            xpos = row["objective"] / 1000
            ax.vlines(
                xpos,
                yi - 0.07,
                yi + 0.07,
                color=METHOD_PALETTE["secondary"],
                linewidth=0.8,
            )
            ax.text(
                xpos + 1.2,
                yi,
                f"{int(row['objective']):,} B; {row['wall_seconds']:.2f} s",
                ha="left",
                va="center",
                fontsize=7,
            )
        ax.set_yticks(y, certificates["label"] + " / " + certificates["order"])
        ax.set_xlabel("Fixed-order traffic objective $E$ [KB]")
        ax.set_title("Machine-checkable fixed-order traffic certificates")
        ax.set_xlim(0, 92)
        ax.set_ylim(-0.55, len(certificates) - 0.4)
        ax.grid(axis="x", alpha=0.3, linewidth=0.5)
        ax.text(
            58,
            1.52,
            "Conv 0 order difference: 24,096 B",
            ha="left",
            va="center",
            fontsize=7,
            color=METHOD_PALETTE["accent_1"],
        )
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=1)

        ax = axes[1]
        status_y = {
            "OPTIMAL": 3,
            "FEASIBLE": 2,
            "FALLBACK_TIMEOUT": 1,
            "FALLBACK_NOT_RUN": 0,
        }
        status_style = {
            "OPTIMAL": (METHOD_PALETTE["secondary"], "o"),
            "FEASIBLE": (METHOD_PALETTE["accent_3"], "^"),
            "FALLBACK_TIMEOUT": (METHOD_PALETTE["accent_1"], "x"),
            "FALLBACK_NOT_RUN": (METHOD_PALETTE["neutral"], "s"),
        }
        provisional = df[df["record_kind"] != "machine_traffic_certificate"].reset_index(drop=True)
        x = np.arange(len(provisional))
        xlabels = []
        for xi, (_, row) in enumerate(provisional.iterrows()):
            y = status_y[row["status"]]
            color, marker = status_style[row["status"]]
            ax.scatter(xi, y, color=color, marker=marker, zorder=3)
            provenance = (
                "artifact" if row["record_kind"] == "machine_feasible_artifact" else "run log"
            )
            xlabels.append(f"{row['label']}\n{provenance}")
            if row["case"] == "Matmul_Case0":
                ax.text(xi, y + 0.18, "gap 4,864 B", ha="center", va="bottom", fontsize=7)
            if row["case"] == "FlashAttention_Case1":
                ax.text(xi, y + 0.18, "gap 576 B", ha="center", va="bottom", fontsize=7)
        ax.set_yticks(
            [0, 1, 2, 3], ["Fallback: not run", "Fallback: timeout", "Feasible", "Optimal"]
        )
        ax.set_ylim(-0.45, 3.45)
        ax.set_xticks(x, xlabels)
        ax.set_xlabel("Evidence provenance")
        ax.set_title("Feasible artifacts and provisional run logs")
        ax.grid(axis="both", alpha=0.3, linewidth=0.5)
        return fig

    return _emit(render, "exact_certificate_scope")


def figure_robustness_boundaries():
    capacity = pd.read_csv(CAPACITY_CSV)
    synthetic = pd.read_csv(SYNTH_CSV)

    def render():
        fig, axes = make_figure("double_col", ncols=2, height=3.55)
        ax = axes[0]
        feasible = capacity[capacity["status"] == "feasible"].copy()
        infeasible = capacity[capacity["status"] != "feasible"].copy()
        styles = [
            (
                "full_extra",
                r"Selected $H=0$ configuration",
                METHOD_PALETTE["primary"],
                "o",
                "-",
            ),
            (
                "blind_extra",
                "Cost-blind ordering comparator",
                METHOD_PALETTE["accent_3"],
                "s",
                "--",
            ),
        ]
        for column, label, color, marker, linestyle in styles:
            ax.plot(
                feasible["L1_capacity"] / 1024,
                feasible[column] / 1000,
                color=color,
                marker=marker,
                linestyle=linestyle,
                label=label,
            )
        top = feasible[["full_extra", "blind_extra"]].max().max() / 1000
        ax.scatter(
            infeasible["L1_capacity"] / 1024,
            [top * 1.03] * len(infeasible),
            color=METHOD_PALETTE["accent_1"],
            marker="x",
            label="Pinned set infeasible",
        )
        first_feasible = feasible.iloc[0]
        ax.annotate(
            "3 KiB selects capfit_id",
            (first_feasible["L1_capacity"] / 1024, first_feasible["full_extra"] / 1000),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=7,
            color=METHOD_PALETTE["primary"],
        )
        ax.set_xlabel("L1 capacity [KiB]")
        ax.set_ylabel("P2 extra traffic [KB]")
        ax.set_title(r"Conv 0 controlled $H=0$ capacity sweep")
        ax.set_ylim(0, top * 1.14)
        ax.grid(axis="both", alpha=0.3, linewidth=0.5)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=1)

        ax = axes[1]
        x = np.arange(len(synthetic))
        bottoms = np.zeros(len(synthetic))
        stacks = [
            ("wins", "Wins", METHOD_PALETTE["secondary"]),
            ("ties", "Ties", METHOD_PALETTE["neutral"]),
            ("losses", "Losses", METHOD_PALETTE["accent_1"]),
        ]
        for column, label, color in stacks:
            vals = synthetic[column].to_numpy()
            ax.bar(
                x,
                vals,
                bottom=bottoms,
                color=color,
                edgecolor="white",
                linewidth=0.6,
                label=label,
            )
            for xi, bottom, value in zip(x, bottoms, vals):
                if value:
                    ax.text(
                        xi,
                        bottom + value / 2,
                        str(int(value)),
                        ha="center",
                        va="center",
                        fontsize=7,
                    )
            bottoms += vals
        ax.set_xticks(x, synthetic["comparison"])
        ax.set_ylabel("Synthetic instances")
        ax.set_title("Internal synthetic non-regression (unvalidated)")
        ax.set_ylim(0, 40)
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3)
        return fig

    return _emit(render, "robustness_boundaries")


def figure_component_attribution():
    """Show selected six-case configurations without implying a factorial design."""
    df = pd.read_csv(ATTRIBUTION_CSV)

    def render():
        fig, ax = make_figure("double_col", height=3.65)
        x = np.arange(len(df))
        specs = [
            (
                "h0_reference_ratio",
                r"Controlled $H=0$ reference",
                METHOD_PALETTE["neutral"],
                "o",
                ":",
            ),
            (
                "best_fit_only_ratio",
                "Best-fit only",
                METHOD_PALETTE["accent_3"],
                "s",
                "--",
            ),
            (
                "frontier_only_ratio",
                "Frontier only",
                METHOD_PALETTE["secondary"],
                "^",
                "-.",
            ),
            (
                "selected_full_ratio",
                r"Selected full $H=0$ configuration",
                METHOD_PALETTE["primary"],
                "D",
                "-",
            ),
        ]
        for column, label, color, marker, linestyle in specs:
            ax.plot(
                x,
                df[column],
                color=color,
                marker=marker,
                linestyle=linestyle,
                label=label,
                zorder=3,
            )

        additive_ratio = df["naive_additive_prediction"] / df["h0_reference_extra"]
        ax.scatter(
            x,
            additive_ratio,
            color=METHOD_PALETTE["accent_1"],
            marker="X",
            label="Naive additive extrapolation",
            zorder=4,
        )
        ax.vlines(
            x,
            df["selected_full_ratio"],
            additive_ratio,
            color=METHOD_PALETTE["accent_1"],
            linewidth=0.8,
            alpha=0.7,
            zorder=2,
        )
        ax.text(
            x[0] + 0.12,
            (additive_ratio.iloc[0] + df["selected_full_ratio"].iloc[0]) / 2,
            "18,484 B beyond naive extrapolation",
            color=METHOD_PALETTE["accent_1"],
            ha="left",
            va="center",
            fontsize=7,
        )
        add_reference_line(ax, 1.0, r"Controlled $H=0$ parity")
        ax.set_xticks(x, df["label"])
        ax.set_ylabel(r"P2 extra / controlled $H=0$ reference")
        ax.set_title("Selected controlled configurations are non-additive")
        ax.set_ylim(0.73, 1.035)
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3)
        return fig

    return _emit(render, "component_attribution")


def figure_all_cases_cost_decomposition():
    """Pair production Scalable v2 and official through delta E=delta V+delta D."""
    df = pd.read_csv(ALL_COST_CSV)

    def render():
        fig, ax = make_figure("double_col", height=3.7)
        x = np.arange(len(df))
        width = 0.32
        ax.bar(
            x - width / 2,
            df["volume_reduction"],
            width,
            color=METHOD_PALETTE["primary"],
            edgecolor="white",
            linewidth=0.6,
            label=r"Volume reduction $\Delta V$",
            zorder=2,
        )
        ax.bar(
            x + width / 2,
            df["generated_reduction"],
            width,
            color=METHOD_PALETTE["accent_3"],
            edgecolor="white",
            linewidth=0.6,
            label=r"Surcharge reduction $\Delta D$",
            zorder=2,
        )
        ax.scatter(
            x,
            df["extra_reduction"],
            color=METHOD_PALETTE["secondary"],
            marker="D",
            label=r"Net reduction $\Delta E=\Delta V+\Delta D$",
            zorder=4,
        )
        for xi, total in zip(x, df["extra_reduction"]):
            ax.text(
                xi,
                total + (160 if total > 0 else 80),
                f"{int(total):+,} B",
                ha="center",
                va="bottom",
                fontsize=7,
            )
        conv1 = df[df["case"] == "Conv_Case1"].iloc[0]
        ax.text(
            x[1] + 0.17,
            conv1["generated_reduction"] - 110,
            r"$D$ rises by 171 B",
            color=METHOD_PALETTE["accent_1"],
            ha="left",
            va="top",
            fontsize=7,
        )
        ax.axhline(0, color="#666666", linewidth=0.8)
        ax.set_xticks(x, df["label"])
        ax.set_ylabel("Official minus Scalable v2 [bytes]")
        ax.set_title(r"Production P2 paired accounting: $\Delta E=\Delta V+\Delta D$")
        ax.set_ylim(-650, 7900)
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3)
        return fig

    return _emit(render, "all_cases_cost_decomposition")


def figure_p2_p3_decoupling():
    """Compare the production P2 and P3 artifacts within the same portfolio."""
    df = pd.read_csv(DECOUPLING_CSV)

    def render():
        fig, ax = make_figure("double_col", height=3.8)
        regular = df["case"] != "Conv_Case1"
        ax.scatter(
            df.loc[regular, "traffic_delta_pct"],
            df.loc[regular, "latency_delta_pct"],
            color=METHOD_PALETTE["primary"],
            marker="o",
            label="P3 artifact vs P2 artifact",
            zorder=3,
        )
        conv1_highlight = df[~regular].iloc[0]
        ax.scatter(
            conv1_highlight["traffic_delta_pct"],
            conv1_highlight["latency_delta_pct"],
            color=METHOD_PALETTE["accent_1"],
            marker="X",
            s=58,
            label="Conv 1 near-zero traffic delta",
            zorder=4,
        )
        ax.axvline(0, color="#666666", linestyle="--", linewidth=0.8)
        ax.axhline(0, color="#666666", linestyle="--", linewidth=0.8)

        offsets = {
            "Conv_Case0": (5, -2),
            "FlashAttention_Case0": (-4, -12),
            "FlashAttention_Case1": (5, 4),
            "Matmul_Case0": (5, -9),
            "Matmul_Case1": (6, 5),
        }
        for _, row in df.iterrows():
            if row["case"] == "Conv_Case1":
                ax.annotate(
                    "Conv 1\n+8 B, -35,985 cycles",
                    (row["traffic_delta_pct"], row["latency_delta_pct"]),
                    xytext=(5, -28),
                    textcoords="offset points",
                    fontsize=7,
                    color=METHOD_PALETTE["accent_1"],
                )
                continue
            dx, dy = offsets[row["case"]]
            ax.annotate(
                row["label"],
                (row["traffic_delta_pct"], row["latency_delta_pct"]),
                xytext=(dx, dy),
                textcoords="offset points",
                fontsize=7,
                color=(METHOD_PALETTE["accent_1"] if row["case"] == "Conv_Case1" else "#333333"),
            )
        ax.text(
            8.7,
            -2.1,
            "P3 trades more traffic\nfor lower latency",
            color=METHOD_PALETTE["accent_1"],
            ha="left",
            va="center",
            fontsize=7,
        )
        ax.set_xlim(-0.5, 15.5)
        ax.set_ylim(-21, 1.5)
        ax.set_xlabel("P3 traffic change relative to P2 artifact [%]")
        ax.set_ylabel("P3 latency change relative to P2 artifact [%]")
        ax.set_title("Within-portfolio P2-to-P3 traffic--latency tradeoff")
        ax.grid(axis="both", alpha=0.3, linewidth=0.5)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2)
        return fig

    return _emit(render, "p2_p3_decoupling")


def figure_objective_example():
    """Refresh the paper's DAG schematic with backed/generated terminology."""

    def render():
        fig, ax = make_figure("double_col", height=3.0)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        op_face = "#EAF2F8"
        op_edge = "#2A5A87"
        mem_face = "#F8E9EE"
        mem_edge = "#B56576"

        def box(x, y, w, h, text, face, edge):
            patch = FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.012,rounding_size=0.01",
                linewidth=1.1,
                facecolor=face,
                edgecolor=edge,
            )
            ax.add_patch(patch)
            ax.text(x + w / 2, y + h / 2, text, ha="center", va="center")
            return patch

        def arrow(x1, y1, x2, y2):
            ax.add_patch(
                FancyArrowPatch(
                    (x1, y1),
                    (x2, y2),
                    arrowstyle="->",
                    mutation_scale=10,
                    linewidth=1.1,
                    color="#555555",
                )
            )

        box(0.08, 0.69, 0.14, 0.14, "ALLOC $b_0$\n(backed)", mem_face, mem_edge)
        box(0.28, 0.64, 0.16, 0.16, "COPY_IN\n$\\{b_0\\}$", op_face, op_edge)
        box(0.50, 0.64, 0.16, 0.16, "COMPUTE\n$\\{b_0,b_1\\}$", op_face, op_edge)
        box(0.72, 0.64, 0.16, 0.16, "COPY_OUT\n$\\{b_1\\}$", op_face, op_edge)
        box(0.50, 0.30, 0.16, 0.14, "ALLOC $b_1$\n(generated)", mem_face, mem_edge)
        box(0.79, 0.30, 0.12, 0.14, "FREE $b_1$", mem_face, mem_edge)
        box(0.27, 0.30, 0.12, 0.14, "FREE $b_0$", mem_face, mem_edge)
        arrow(0.22, 0.74, 0.28, 0.72)
        arrow(0.44, 0.72, 0.50, 0.72)
        arrow(0.66, 0.72, 0.72, 0.72)
        arrow(0.58, 0.44, 0.58, 0.64)
        arrow(0.52, 0.64, 0.39, 0.44)
        arrow(0.80, 0.64, 0.85, 0.44)

        ax.text(
            0.15,
            0.55,
            "Backed spill bytes $C$\nreload charge: $1\\times$",
            color=METHOD_PALETTE["secondary"],
            ha="center",
            va="center",
        )
        ax.text(
            0.80,
            0.54,
            "Generated spill bytes $D$\nwriteback + reload: $2\\times$",
            color=METHOD_PALETTE["accent_1"],
            ha="center",
            va="center",
        )
        ax.text(
            0.50, 0.10, r"Canonical P2 identity: $E=C+2D=(C+D)+D=V+D$", ha="center", va="center"
        )
        handles = [
            Patch(facecolor=mem_face, edgecolor=mem_edge, label="Cache management"),
            Patch(facecolor=op_face, edgecolor=op_edge, label="Operation"),
        ]
        ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2)
        return fig

    return _emit(render, "e1_dag_example")


def build_all() -> dict[str, pd.DataFrame]:
    data = prepare_data()
    figure_public_p2_p3()
    figure_conv0_method_path()
    figure_cost_identity()
    figure_exact_certificate_scope()
    figure_robustness_boundaries()
    figure_component_attribution()
    figure_all_cases_cost_decomposition()
    figure_p2_p3_decoupling()
    figure_objective_example()
    return data


def main() -> None:
    data = build_all()
    print("Built audited v2 evidence:")
    for name, frame in data.items():
        print(f"  {name}: {len(frame)} rows")


if __name__ == "__main__":
    main()
