# %% [markdown]
# ## 8. C1 generality check
#
# A synthetic instance controls the clean/dirty reserve under the same
# structure, checking that the 2× spill-cost asymmetry is not a Conv artifact.

# %%
show_png("e11_synth_generality.png")
display(e11_ablation)

best_clean = e11_ablation[(e11_ablation["reserve"] == "clean") & (e11_ablation["order"] == "capfit_id")].iloc[0]
best_dirty = e11_ablation[(e11_ablation["reserve"] == "dirty") & (e11_ablation["order"] == "capfit_id")].iloc[0]
synthetic_check = pd.DataFrame(
    [
        {"metric": "clean reserve extra", "value": int(best_clean["extra"])},
        {"metric": "dirty reserve extra", "value": int(best_dirty["extra"])},
        {"metric": "spill count clean/dirty", "value": f"{int(best_clean['spills'])} / {int(best_dirty['spills'])}"},
        {"metric": "peak total clean/dirty", "value": f"{int(best_clean['peak_total'])} / {int(best_dirty['peak_total'])}"},
    ]
)
display(synthetic_check)

note(
    "The robust statement is clean=1536, dirty=3072 with the same spill count, so "
    "dirty extra is exactly 2× — the asymmetry generalizes beyond Conv."
)
