"""ks_core.plotting — CVPR-standard academic figure style.

Single source of truth for all figure aesthetics in this project.
See ``docs/plotting_standards.md`` for the full specification.

Usage::

    from ks_core.plotting import setup_academic_style, make_figure, savefig_academic

    fig, ax = make_figure("double_col")
    ax.plot(x, y)
    savefig_academic(fig, "output/my_figure.png")
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np

# ── Method colour palette (≤ 6 methods) ──────────────────────────────────
METHOD_PALETTE = {
    "primary":   "#4C72B0",  # steel blue
    "secondary": "#55A868",  # muted green
    "accent_1":  "#C44E52",  # soft red
    "accent_2":  "#8172B2",  # lavender purple
    "accent_3":  "#DD8452",  # warm orange
    "neutral":   "#937860",  # taupe
}

METHOD_COLOR_LIST = list(METHOD_PALETTE.values())

# ── Recommended colormaps ─────────────────────────────────────────────────
COLORMAPS = {
    "heatmap":       "inferno",   # DAG density / node weight heatmap
    "residual_pos":  "YlOrRd",    # single-sided residual (≥ 0)
    "residual_diff": "RdBu_r",    # diverging residual (±)
    "coverage":      "viridis",   # count / coverage / utilisation
}

# ── Figure sizes (width, height) in inches ────────────────────────────────
FIGURE_SIZES = {
    "single_col":   (3.5, 2.6),
    "one_half_col": (5.5, 3.5),
    "double_col":   (7.2, 4.0),
    "notebook":     (8.0, 5.0),
}

# ── Marker cycle for colour-blind safety ──────────────────────────────────
MARKER_CYCLE = ["o", "s", "^", "D", "v", "P", "X", "*"]

# ── Line-style cycle ──────────────────────────────────────────────────────
LINESTYLE_CYCLE = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]

# ---------------------------------------------------------------------------
# rcParams dictionary (the single source of truth)
# ---------------------------------------------------------------------------

ACADEMIC_RCPARAMS: dict = {
    # ── Font ──
    "font.family":       "serif",
    "font.serif":        ["Times New Roman", "Times", "DejaVu Serif", "serif"],
    "font.size":         9,
    "mathtext.fontset":  "stix",

    # ── Axes ──
    "axes.titlesize":    10,
    "axes.titleweight":  "normal",
    "axes.labelsize":    9,
    "axes.labelweight":  "normal",
    "axes.linewidth":    0.8,
    "axes.spines.top":   False,
    "axes.spines.right": False,

    # ── Ticks ──
    "xtick.labelsize":   8,
    "ytick.labelsize":   8,
    "xtick.direction":   "out",
    "ytick.direction":   "out",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size":  3.5,
    "ytick.major.size":  3.5,
    "xtick.minor.visible": False,
    "ytick.minor.visible": False,

    # ── Legend ──
    "legend.fontsize":      8,
    "legend.frameon":       False,
    "legend.handlelength":  1.5,
    "legend.handletextpad": 0.5,
    "legend.borderpad":     0.4,

    # ── Lines ──
    "lines.linewidth":  1.4,
    "lines.markersize": 5,

    # ── Grid ──
    "axes.grid":     False,
    "grid.alpha":    0.3,
    "grid.linewidth": 0.5,
    "grid.color":    "#cccccc",

    # ── Figure ──
    "figure.dpi":       300,
    "figure.facecolor": "white",
    "figure.constrained_layout.use": True,

    # ── Saving ──
    "savefig.dpi":       300,
    "savefig.bbox":      "tight",
    "savefig.pad_inches": 0.03,
    "savefig.facecolor": "white",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_academic_style() -> None:
    """Apply the project-wide CVPR-standard academic figure style.

    Must be called at the beginning of every figure_* function or notebook cell
    that produces figures.  See ``docs/plotting_standards.md`` for the full
    specification.
    """
    plt.rcParams.update(ACADEMIC_RCPARAMS)

    # Enable retina displays in Jupyter notebooks for crisp figures
    try:
        from IPython import get_ipython
        ipy = get_ipython()
        if ipy is not None:
            ipy.run_line_magic("config", "InlineBackend.figure_format = 'retina'")
    except Exception:
        pass


def savefig_academic(
    fig: plt.Figure,
    path: str | Path,
    *,
    dpi: int = 300,
    close: bool = True,
    inline_dpi: int = 300,
) -> Path:
    """Save a figure following the project saving conventions.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to save.
    path : str or Path
        Destination file path.  Parent directories are created automatically.
        Use ``.pdf`` for paper submission, ``.png`` for notebook display.
    dpi : int, optional
        Resolution in dots per inch.  Must be ≥ 300 for paper figures.
    close : bool, optional
        If *True* (default), close the figure after saving to free memory.
    inline_dpi : int, optional
        DPI to assign to ``fig.dpi`` **after** saving.  When the caller
        returns the figure as the last cell expression, Jupyter's
        ``_repr_png_()`` uses ``fig.dpi`` to render the inline preview.
        The default is 300 so executed notebooks show the same high-resolution
        figure that is saved to disk.

    Returns
    -------
    Path
        The resolved path to the saved file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    # Keep notebook inline display at publication DPI.
    fig.dpi = inline_dpi
    if close:
        plt.close(fig)
    return path


def get_method_style(
    index: int,
) -> dict:
    """Return a consistent (color, marker, linestyle) dict for method *index*.

    Use this to cycle through visual styles when plotting multiple methods,
    ensuring colour-blind safety (distinct markers + linestyles alongside
    colours).

    Parameters
    ----------
    index : int
        Zero-based method index.

    Returns
    -------
    dict
        Keys: ``color``, ``marker``, ``linestyle``.
    """
    return {
        "color":     METHOD_COLOR_LIST[index % len(METHOD_COLOR_LIST)],
        "marker":    MARKER_CYCLE[index % len(MARKER_CYCLE)],
        "linestyle": LINESTYLE_CYCLE[index % len(LINESTYLE_CYCLE)],
    }


def add_reference_line(
    ax: plt.Axes,
    value: float,
    label: str,
    *,
    axis: Literal["x", "y"] = "y",
    color: str = "#666666",
    linewidth: float = 0.9,
) -> None:
    """Add a dashed reference / threshold line to *ax*.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    value : float
        Position of the reference line.
    label : str
        Legend label describing the line's meaning.
    axis : {"x", "y"}, optional
        Which axis the line is parallel to.
    color : str, optional
        Line colour.
    linewidth : float, optional
        Line width.
    """
    fn = ax.axhline if axis == "y" else ax.axvline
    fn(value, ls="--", color=color, linewidth=linewidth, label=label, zorder=1)


def format_colorbar(
    cbar,
    label: str,
    *,
    fontsize: int = 8,
) -> None:
    """Apply standard formatting to a colorbar.

    Parameters
    ----------
    cbar : matplotlib.colorbar.Colorbar
        The colorbar to format.
    label : str
        Descriptive label including units, e.g. ``"Latency [cycles]"``.
    fontsize : int, optional
        Label font size.
    """
    cbar.set_label(label, fontsize=fontsize)
    cbar.ax.tick_params(labelsize=fontsize)


def make_figure(
    layout: Literal["single_col", "one_half_col", "double_col", "notebook"] = "single_col",
    *,
    nrows: int = 1,
    ncols: int = 1,
    height: float | None = None,
    **subplot_kw,
) -> tuple[plt.Figure, np.ndarray | plt.Axes]:
    """Create a figure with standardised sizing.

    Parameters
    ----------
    layout : str
        One of the predefined layout keys in :data:`FIGURE_SIZES`.
    nrows, ncols : int
        Subplot grid dimensions.
    height : float or None
        Override the default height (inches).  Width is always from
        the layout preset.
    **subplot_kw
        Extra keyword arguments forwarded to ``plt.subplots``.

    Returns
    -------
    fig, axes
    """
    setup_academic_style()
    w, h = FIGURE_SIZES[layout]
    if height is not None:
        h = height
    # Scale height with number of rows
    if nrows > 1:
        h = h * nrows * 0.7  # slight compression per row
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, h), **subplot_kw)
    return fig, axes


# ---------------------------------------------------------------------------
# Project figure vocabulary — shared by every notebook that plots benchmark
# results (lifted out of individual notebooks so labels/colours stay in sync).
# ---------------------------------------------------------------------------

# Canonical left-to-right ordering of the six benchmark instances.
CASE_ORDER = [
    "Conv_Case0",
    "Conv_Case1",
    "FlashAttention_Case0",
    "FlashAttention_Case1",
    "Matmul_Case0",
    "Matmul_Case1",
]

# Compact axis labels for the benchmark instances.
CASE_LABELS = {
    "Conv_Case0": "Conv 0",
    "Conv_Case1": "Conv 1",
    "FlashAttention_Case0": "FA 0",
    "FlashAttention_Case1": "FA 1",
    "Matmul_Case0": "Matmul 0",
    "Matmul_Case1": "Matmul 1",
}

# Human-readable labels for schedule-order / method keys.
ORDER_LABELS = {
    "capfit_id": "CapFit",
    "p1": "P1",
    "id_raw": "ID",
    "min_id": "Min-ID",
    "baseline": "Base",
    "cp_list": "Critical-path",
    "cp_free_first": "Delayed-free",
    "pressure_uniform": "Uniform pressure",
    "goodman_hsu": "Goodman--Hsu",
    "ours": "Ours",
    "phi_best": r"$\Phi$-best",
    "ratio_all": "All orders",
    "ratio_nearopt": "Near-optimal",
}

# Stable colour assignment per order/method, drawn from METHOD_PALETTE so the
# "ours" family always reads as the primary colour and baselines as accents.
ORDER_COLORS = {
    "capfit_id": METHOD_PALETTE["primary"],
    "ours": METHOD_PALETTE["primary"],
    "phi_best": METHOD_PALETTE["primary"],
    "p1": METHOD_PALETTE["secondary"],
    "cp_free_first": METHOD_PALETTE["secondary"],
    "id_raw": METHOD_PALETTE["accent_3"],
    "pressure_uniform": METHOD_PALETTE["accent_2"],
    "min_id": METHOD_PALETTE["neutral"],
    "goodman_hsu": METHOD_PALETTE["neutral"],
    "baseline": METHOD_PALETTE["accent_1"],
    "cp_list": METHOD_PALETTE["accent_1"],
    "ratio_all": "#c9c9c9",
    "ratio_nearopt": METHOD_PALETTE["primary"],
}


def case_label(case) -> str:
    """Compact display label for a benchmark case key."""
    return CASE_LABELS.get(str(case), str(case).replace("_Case", " "))


def order_label(name) -> str:
    """Human-readable label for a schedule-order / method key."""
    return ORDER_LABELS.get(str(name), str(name))


def order_color(name, default: str = METHOD_PALETTE["neutral"]) -> str:
    """Stable colour for a schedule-order / method key."""
    return ORDER_COLORS.get(str(name), default)


def compact_count(value) -> str:
    """Format a count compactly (e.g. ``1.2M``, ``34k``, ``128``)."""
    value = float(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 100_000:
        return f"{value / 1_000:.0f}k"
    if value >= 10_000:
        return f"{value / 1_000:.1f}k"
    if abs(value - round(value)) < 1e-9:
        return f"{value:.0f}"
    return f"{value:.2g}"


def compact_ratio(value) -> str:
    """Format a ratio compactly with an ``x`` suffix (e.g. ``2.3x``)."""
    value = float(value)
    if value >= 10:
        return f"{value:.0f}x"
    if value >= 1:
        return f"{value:.1f}x"
    return f"{value:.2f}x"


def annotate_bars(ax, bars, values=None, formatter=compact_count, *,
                  rotation=90, fontsize=7.8, offset=2, min_value=0.0) -> None:
    """Annotate each bar in *bars* with its (formatted) value."""
    values = values if values is not None else [bar.get_height() for bar in bars]
    for bar, value in zip(bars, values):
        value = float(value)
        if value <= min_value:
            continue
        ax.annotate(
            formatter(value),
            xy=(bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, offset),
            textcoords="offset points",
            ha="center",
            va="bottom",
            rotation=rotation,
            fontsize=fontsize,
            clip_on=False,
        )


def style_bar_axes(ax, *, xlabel="Benchmark case", ylabel=None, grid_alpha=0.22) -> None:
    """Apply the project's standard bar-chart axis styling."""
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.tick_params(axis="x", labelsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(axis="y", alpha=grid_alpha, linewidth=0.5)
    ax.grid(False, which="minor", axis="y")
    ax.tick_params(axis="y", which="minor", length=0)


def place_bar_legend(ax, *, ncol=3, y=1.03):
    """Place a frameless legend above the axes, left-aligned."""
    return ax.legend(
        ncol=ncol,
        loc="lower left",
        bbox_to_anchor=(0.0, y),
        borderaxespad=0.0,
        frameon=False,
    )


def grouped_offsets(n, width):
    """Symmetric x-offsets for *n* grouped bars of the given *width*."""
    return [(i - (n - 1) / 2) * width for i in range(n)]
