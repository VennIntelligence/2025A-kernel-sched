# %% [markdown]
# ## 3. Solver architecture
#
# The method is not a single heuristic. It is a small portfolio of generic
# candidate orders evaluated by the true official key, so adding a candidate can
# only improve or tie the selected result.

# %%
architecture = pd.DataFrame(
    [
        {"component": "P1 order", "implementation": "memory-aware list scheduler", "purpose": "minimize the official P1 residency key"},
        {"component": "P2/P3 candidate orders", "implementation": "capfit_id, p1, id_raw", "purpose": "cover capacity-throttled, P1-optimized, and native-id residency patterns"},
        {"component": "physical placement", "implementation": "address-ordered first fit over free intervals", "purpose": "assign cache offsets and expose overflow events"},
        {"component": "spill victim", "implementation": "cost-aware Belady-style next-use score", "purpose": "prefer far-future and cheaper clean COPY_IN buffers"},
        {"component": "P2 selection key", "implementation": "(extra, spills, time)", "purpose": "match the traffic-first objective"},
        {"component": "P3 selection key", "implementation": "(time, extra, spills)", "purpose": "match the time-first objective"},
        {"component": "P3 prefetch grid", "implementation": "H in {0, 5, 40, 80, 120}", "purpose": "hide SPILL_IN latency without evicting other buffers during prefetch"},
    ]
)
display(architecture)

note(
    "The candidate orders do not depend on case names. The value of `id_raw` is "
    "that it preserves native block flow, making clean COPY_IN buffers more "
    "available at overflow windows."
)
