"""Shared type definitions for kernel scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class MemoryType(str, Enum):
    """On-chip memory types for the neural network processor."""
    L1 = "L1"
    L0A = "L0A"
    L0B = "L0B"
    L0C = "L0C"
    UB = "UB"


class OpType(str, Enum):
    """Instruction / operation types."""
    ALLOC = "ALLOC"
    FREE = "FREE"
    COPY_IN = "COPY_IN"
    COPY_OUT = "COPY_OUT"
    MOVE = "MOVE"
    CONV = "CONV"
    CONV_ADD = "CONV_ADD"
    MATMUL = "MATMUL"
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    MAX = "MAX"
    EXP = "EXP"
    REC = "REC"
    ROWMAX = "ROWMAX"
    ROWSUM = "ROWSUM"
    COMPACT = "COMPACT"
    D2S = "D2S"
    COPY = "COPY"


class Pipe(str, Enum):
    """Execution pipelines on the processor."""
    MTE1 = "MTE1"
    MTE2 = "MTE2"
    MTE3 = "MTE3"
    CUBE = "CUBE"
    VECTOR = "VECTOR"
    FIXP = "FIXP"


@dataclass
class Node:
    """A node in the computation DAG."""
    id: int
    op: str
    pipe: str | None = None
    cycles: int = 0
    bufs: list[int] = field(default_factory=list)
    buf_id: int | None = None
    size: int = 0
    mem_type: str | None = None


@dataclass
class Edge:
    """A dependency edge in the DAG."""
    src: int
    dst: int
    edge_type: str = "data"  # "data" | "control"


@dataclass
class ProblemInstance:
    """A complete problem instance (one case, one problem variant)."""
    case_name: str          # e.g. "Conv_Case0"
    problem_id: int         # 1, 2, or 3
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    # Hardware constraints (from problem statement)
    max_l1: int = 0
    max_ub: int = 0
    max_l0a_count: int = 0
    max_l0b_count: int = 0
    max_l0c_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpillDecision:
    """A spill/reload decision for Problem 2/3."""
    buf_id: int
    spill_at_step: int
    reload_at_step: int
    extra_bytes: int = 0


@dataclass
class Schedule:
    """Output of an algorithm: a complete scheduling solution."""
    case_name: str
    problem_id: int
    algorithm: str
    # Core output: ordered list of node IDs
    order: list[int] = field(default_factory=list)
    # Problem 2/3: spill decisions
    spills: list[SpillDecision] = field(default_factory=list)
    # Computed metrics (filled by simulator)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class Metrics:
    """Standardized evaluation metrics."""
    total_time: int = 0       # Total execution cycles
    num_spills: int = 0       # Number of spill operations
    extra_memory: int = 0     # Extra off-chip memory used
    violations: int = 0       # Constraint violations (must be 0)
    schedule_length: int = 0  # Number of steps in schedule
