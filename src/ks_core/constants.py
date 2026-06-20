"""ks_core.constants — hardware constants shared across the project.

Single source of truth for values that would otherwise be duplicated between
the solver, the metrics layer, the data-inventory utilities, and the paper
data emitters.  Import from here; never re-declare these literals locally.
"""

from __future__ import annotations

# On-chip cache / buffer capacities (bytes) for the target NPU.
#
# Imported by:
#   - ks_core.solver                 (the promoted solver, spill assignment)
#   - ks_core.evaluator              (schedule simulator / metrics)
#   - ks_core.data_utils             (data inventory / benchmark tables)
#   - scripts/paper/inv_inventory.py, prob_metrics.py (paper CSV emitters)
CACHE_CAPACITIES: dict[str, int] = {
    "L1": 4096,
    "UB": 1024,
    "L0A": 256,
    "L0B": 256,
    "L0C": 512,
}
