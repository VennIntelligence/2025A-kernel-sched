"""Analysis helpers for schedule characterization notebooks."""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import cycle
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ks_core.evaluator import CACHE_CAPACITIES, CACHE_TYPES, compute_total_time
from ks_core.plotting import COLORMAPS, METHOD_COLOR_LIST, make_figure
from ks_core.types import Edge, Node, ProblemInstance

PIPE_ORDER = ("MTE1", "MTE2", "MTE3", "CUBE", "VECTOR", "FIXP")
BASELINE_CASE_ORDER = (
    "FlashAttention_Case0",
    "FlashAttention_Case1",
    "Matmul_Case0",
    "Matmul_Case1",
    "Conv_Case0",
    "Conv_Case1",
)


def compute_vstay_curve(order: list[int], nodes: dict[int, Node]) -> dict[str, list[int]]:
    """Compute the V_stay curve for every cache type along a schedule order."""
    current = {cache: 0 for cache in CACHE_TYPES}
    curves = {cache: [0] for cache in CACHE_TYPES}

    for node_id in order:
        node = nodes.get(node_id)
        if node is not None and node.mem_type in current:
            if node.op == "ALLOC":
                current[node.mem_type] += node.size
            elif node.op == "FREE":
                current[node.mem_type] -= node.size
        for cache in CACHE_TYPES:
            curves[cache].append(current[cache])

    return curves


def compute_pipe_timeline(
    order: list[int],
    nodes: dict[int, Node],
    edges: list[Edge],
) -> list[dict[str, Any]]:
    """Compute start/end time records for nodes that execute on a pipeline."""
    predecessors: dict[int, list[int]] = defaultdict(list)
    for edge in edges:
        predecessors[edge.dst].append(edge.src)

    end_time: dict[int, int] = {}
    pipe_ready: dict[str, int] = defaultdict(int)
    timeline: list[dict[str, Any]] = []

    for node_id in order:
        node = nodes.get(node_id)
        if node is None:
            continue

        start = max((end_time.get(pred, 0) for pred in predecessors[node_id]), default=0)
        if node.pipe:
            start = max(start, pipe_ready[node.pipe])

        finish = start + node.cycles
        end_time[node_id] = finish

        if node.pipe:
            pipe_ready[node.pipe] = finish
            timeline.append(
                {
                    "pipe": node.pipe,
                    "start_time": start,
                    "end_time": finish,
                    "node_id": node_id,
                    "op": node.op,
                }
            )

    return timeline


def compute_pipe_utilization(timeline: list[dict[str, Any]], total_time: int) -> dict[str, float]:
    """Compute busy_time / total_time for every pipeline present in the timeline."""
    busy_time: Counter[str] = Counter()
    for item in timeline:
        busy_time[item["pipe"]] += max(0, item["end_time"] - item["start_time"])

    pipes = [pipe for pipe in PIPE_ORDER if pipe in busy_time]
    pipes.extend(sorted(set(busy_time) - set(pipes)))
    return {pipe: busy_time[pipe] / total_time if total_time else 0.0 for pipe in pipes}


def spill_buffer_stats(
    instance: ProblemInstance,
    spill_entries: list[tuple[int, int]],
) -> pd.DataFrame:
    """Summarize spilled buffer attributes and repeated spill counts."""
    spill_counts = Counter(buf_id for buf_id, _offset in spill_entries)
    allocs = {
        node.buf_id: node
        for node in instance.nodes
        if node.op == "ALLOC" and node.buf_id is not None
    }
    rows = [
        {
            "buf_id": buf_id,
            "mem_type": allocs[buf_id].mem_type,
            "size": allocs[buf_id].size,
            "spill_count": spill_count,
        }
        for buf_id, spill_count in sorted(spill_counts.items())
        if buf_id in allocs
    ]
    return pd.DataFrame(rows, columns=["buf_id", "mem_type", "size", "spill_count"])


def schedule_order_deviation(order: list[int]) -> pd.Series:
    """Return position_in_schedule[node_id] - node_id for every scheduled node."""
    return pd.Series(
        {node_id: position - node_id for position, node_id in enumerate(order)},
        name="deviation",
    ).sort_index()


def plot_schedule_order_panel(
    p1_orders: Mapping[str, list[int]],
    case_order: list[str] | None = None,
):
    """Plot scheduled position against original node id for each case."""
    cases = _ordered_cases(p1_orders, case_order)
    fig, axes = make_figure("double_col", nrows=2, ncols=3)

    for ax, case in zip(_flat_axes(axes), cases):
        deviation = schedule_order_deviation(p1_orders[case])
        node_ids = deviation.index.to_numpy()
        positions = node_ids + deviation.to_numpy()
        point_size = 0.6 if len(node_ids) > 10_000 else 2.0

        ax.scatter(node_ids, positions, s=point_size, alpha=0.45, linewidths=0)
        limit = max(int(node_ids.max()), int(positions.max()))
        ax.plot([0, limit], [0, limit], "--", color="#555555", linewidth=0.8)
        ax.set_title(_case_label(case))
        ax.set_xlabel("Node ID")
        ax.set_ylabel("Schedule position")

    _hide_unused_axes(axes, len(cases))
    return fig


def plot_vstay_curves_panel(
    p1_instances: Mapping[str, ProblemInstance],
    p1_orders: Mapping[str, list[int]],
    cache_type: str,
    case_order: list[str] | None = None,
):
    """Plot V_stay curves for one cache type across all cases."""
    cases = _ordered_cases(p1_orders, case_order)
    curves_by_case = {
        case: compute_vstay_curve(p1_orders[case], _node_map(p1_instances[case]))[cache_type]
        for case in cases
    }
    if cache_type != "L1":
        cases = [case for case in cases if max(curves_by_case[case]) > 0]
        if not cases:
            return None

    nrows, ncols = _panel_grid(len(cases))
    fig, axes = make_figure("double_col", nrows=nrows, ncols=ncols)
    capacity = CACHE_CAPACITIES.get(cache_type)

    for ax, case in zip(_flat_axes(axes), cases):
        curve = curves_by_case[case]
        peak = max(curve)
        peak_step = curve.index(peak)

        ax.plot(range(len(curve)), curve, color=METHOD_COLOR_LIST[0], linewidth=1.1)
        if capacity is not None:
            ax.axhline(
                capacity,
                color="#555555",
                linestyle="--",
                linewidth=0.8,
                label=f"{cache_type} capacity",
            )
        ax.scatter([peak_step], [peak], s=14, color=METHOD_COLOR_LIST[2], zorder=3)
        ax.annotate(f"Peak {peak}", (peak_step, peak), xytext=(4, 4), textcoords="offset points")
        ax.set_title(_case_label(case))
        ax.set_xlabel("Schedule step")
        ax.set_ylabel(f"{cache_type} V_stay")

    _hide_unused_axes(axes, len(cases))
    return fig


def plot_pipe_timeline(timeline: list[dict[str, Any]], case_name: str):
    """Plot a pipeline Gantt chart for one case."""
    from matplotlib.patches import Patch

    fig, ax = make_figure("double_col", height=2.8)
    if not timeline:
        ax.text(0.5, 0.5, "No pipelined nodes", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return fig

    frame = pd.DataFrame(timeline).sort_values(["start_time", "end_time", "node_id"])
    pipes = [pipe for pipe in PIPE_ORDER if pipe in set(frame["pipe"])]
    pipes.extend(sorted(set(frame["pipe"]) - set(pipes)))
    pipe_y = {pipe: index for index, pipe in enumerate(pipes)}
    op_colors = {
        op: color
        for op, color in zip(sorted(frame["op"].unique()), cycle(METHOD_COLOR_LIST), strict=False)
    }

    for row in frame.itertuples(index=False):
        duration = row.end_time - row.start_time
        if duration <= 0:
            continue
        ax.broken_barh(
            [(row.start_time, duration)],
            (pipe_y[row.pipe] - 0.35, 0.7),
            facecolors=op_colors[row.op],
            edgecolors="none",
            alpha=0.9,
        )

    handles = [
        Patch(facecolor=color, edgecolor="none", label=op)
        for op, color in sorted(op_colors.items(), key=lambda item: item[0])
    ]
    ax.set_yticks(range(len(pipes)), pipes)
    ax.set_xlabel("Time (cycles)")
    ax.set_ylabel("Pipe")
    ax.set_title(f"{_case_label(case_name)}: P1 Pipeline Timeline")
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), title="Op")
    return fig


def pipe_utilization_table(
    p1_instances: Mapping[str, ProblemInstance],
    p1_orders: Mapping[str, list[int]],
    case_order: list[str] | None = None,
) -> pd.DataFrame:
    """Compute pipe utilization rows for all P1 baseline cases."""
    rows = []
    for case in _ordered_cases(p1_orders, case_order):
        instance = p1_instances[case]
        nodes = _node_map(instance)
        timeline = compute_pipe_timeline(p1_orders[case], nodes, instance.edges)
        total_time = compute_total_time(p1_orders[case], nodes, instance.edges)
        utilization = compute_pipe_utilization(timeline, total_time)
        rows.append({"case": case, **{pipe: utilization.get(pipe, 0.0) for pipe in PIPE_ORDER}})
    return pd.DataFrame(rows).set_index("case")


def plot_pipe_utilization_heatmap(utilization: pd.DataFrame):
    """Plot a case-by-pipe utilization heatmap."""
    matrix = utilization.reindex(columns=PIPE_ORDER, fill_value=0.0).T * 100
    fig, ax = make_figure("double_col", height=3.1)
    image = ax.imshow(matrix, cmap=COLORMAPS["coverage"], vmin=0, vmax=max(1.0, matrix.max().max()))

    ax.set_xticks(range(len(matrix.columns)), [_case_label(case) for case in matrix.columns])
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    ax.set_xlabel("Case")
    ax.set_ylabel("Pipe")
    ax.set_title("P1 Pipeline Utilization")
    ax.tick_params(axis="x", rotation=30)

    for row_index, pipe in enumerate(matrix.index):
        for col_index, case in enumerate(matrix.columns):
            value = matrix.loc[pipe, case]
            text_color = "black" if value >= matrix.max().max() * 0.55 else "white"
            ax.text(
                col_index,
                row_index,
                f"{value:.1f}%",
                ha="center",
                va="center",
                color=text_color,
            )

    cbar = fig.colorbar(image, ax=ax, shrink=0.85)
    cbar.set_label("Utilization (%)")
    return fig


def spill_summary_table(
    p2_instances: Mapping[str, ProblemInstance],
    p2_spills: Mapping[str, list[tuple[int, int]]],
    case_order: list[str] | None = None,
) -> pd.DataFrame:
    """Group P2 spilled buffers by case and memory type."""
    rows = []
    for case in _ordered_cases(p2_spills, case_order):
        stats = spill_buffer_stats(p2_instances[case], p2_spills[case])
        grouped = stats.groupby("mem_type", as_index=False).agg(
            spill_buffers=("buf_id", "count"),
            spill_events=("spill_count", "sum"),
            total_size=("size", "sum"),
        )
        rows.extend({"case": case, **row} for row in grouped.to_dict("records"))
    return pd.DataFrame(
        rows,
        columns=["case", "mem_type", "spill_buffers", "spill_events", "total_size"],
    )


def plot_spill_size_boxplot(
    p2_instances: Mapping[str, ProblemInstance],
    p2_spills: Mapping[str, list[tuple[int, int]]],
    case_order: list[str] | None = None,
):
    """Plot P2 spilled-buffer size distributions by case."""
    cases = _ordered_cases(p2_spills, case_order)
    data = []
    for case in cases:
        stats = spill_buffer_stats(p2_instances[case], p2_spills[case])
        repeated = stats.loc[stats.index.repeat(stats["spill_count"]), "size"]
        data.append(repeated.to_numpy())

    fig, ax = make_figure("double_col", height=3.2)
    ax.boxplot(data, tick_labels=[_case_label(case) for case in cases], showfliers=True)
    ax.set_xlabel("Case")
    ax.set_ylabel("Spilled buffer size")
    ax.set_title("P2 Spilled Buffer Size Distribution")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.25)
    return fig


def baseline_summary_table(
    metrics: pd.DataFrame,
    utilization: pd.DataFrame,
    case_order: list[str] | None = None,
) -> pd.DataFrame:
    """Build the final baseline characteristics summary table."""
    metrics = _normalize_problem_column(metrics)
    indexed = metrics.set_index(["case", "problem"])
    cases = case_order or sorted(metrics["case"].unique())
    rows = []

    for case in cases:
        p1 = indexed.loc[(case, 1)]
        p2 = indexed.loc[(case, 2)]
        p3 = indexed.loc[(case, 3)]
        top_pipe = utilization.loc[case].idxmax()
        top_utilization = utilization.loc[case, top_pipe] * 100

        rows.append(
            {
                "case": case,
                "max_L1": int(p1["max_L1"]),
                "max_UB": int(p1["max_UB"]),
                "L1_overflow_ratio": round(p1["max_L1"] / CACHE_CAPACITIES["L1"], 2),
                "P1_time": int(p1["time"]),
                "P2_spills": int(p2["spills"]),
                "P2_extra": int(p2["extra"]),
                "P2_time": int(p2["time"]),
                "P3_time": int(p3["time"]),
                "P2/P1_time_ratio": round(p2["time"] / p1["time"], 2),
                "P3/P1_time_ratio": round(p3["time"] / p1["time"], 2),
                "top_pipe": top_pipe,
                "top_pipe_utilization_%": round(top_utilization, 1),
            }
        )

    return pd.DataFrame(rows)


def _node_map(instance: ProblemInstance) -> dict[int, Node]:
    return {node.id: node for node in instance.nodes}


def _ordered_cases(data: Mapping[str, Any], case_order: list[str] | None) -> list[str]:
    if case_order is None:
        return sorted(data)
    return [case for case in case_order if case in data]


def _case_label(case: str) -> str:
    return case.replace("_", " ")


def _flat_axes(axes) -> np.ndarray:
    return np.asarray(axes).reshape(-1)


def _hide_unused_axes(axes, used: int) -> None:
    for ax in _flat_axes(axes)[used:]:
        ax.set_visible(False)


def _panel_grid(count: int) -> tuple[int, int]:
    ncols = min(3, max(1, count))
    return int(np.ceil(count / ncols)), ncols


def _normalize_problem_column(metrics: pd.DataFrame) -> pd.DataFrame:
    normalized = metrics.copy()
    normalized["problem"] = normalized["problem"].map(
        lambda value: int(str(value).removeprefix("P"))
    )
    return normalized
