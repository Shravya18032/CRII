# #crii_engine.py/hybrid_crii.py
# import pandas as pd
# from sklearn.preprocessing import MinMaxScaler

# # Load physical CRII data
# crii_df = pd.read_csv("data/crii_results.csv")

# # Load CLIP scores
# clip_df = pd.read_csv("data/clip_scores.csv")

# # Create mapping (assuming image names like grid_0.jpg)
# clip_df["grid_id"] = clip_df["image"].str.extract(r'(\d+)').astype(int)

# # Merge
# df = crii_df.merge(clip_df, on="grid_id")

# # Normalize CLIP scores
# scaler = MinMaxScaler()

# df[["clip_flood", "clip_heat", "clip_veg", "clip_urban"]] = scaler.fit_transform(
#     df[["flood_score", "heat_score", "vegetation_score", "urban_score"]]
# )

# # Combine semantic scores
# df["clip_combined"] = (
#     df["clip_flood"] +
#     df["clip_heat"] +
#     df["clip_veg"] +
#     df["clip_urban"]
# ) / 4

# # Final Hybrid CRII
# df["hybrid_crii"] = (
#     0.7 * df["crii"] +      # physical
#     0.3 * df["clip_combined"]  # semantic
# )

# # Classification
# def classify(val):
#     if val < 0.25:
#         return "Low"
#     elif val < 0.5:
#         return "Moderate"
#     elif val < 0.75:
#         return "High"
#     else:
#         return "Critical"

# df["hybrid_risk"] = df["hybrid_crii"].apply(classify)

# # Save
# df.to_csv("data/hybrid_crii_results.csv", index=False)

# print("Hybrid CRII computed")
















# crii_engine/hybrid_crii.py
#
# FIX APPLIED: Unified risk classification thresholds to 0.25 / 0.50 / 0.75.
# Original used different thresholds than compute_crii_india.py (0.2/0.4/0.6),
# causing the same location to get different risk categories from each file.
#
# NOTE: CLIP scoring works best with ground-level photos. If you are using
# satellite imagery, replace CLIPModel with RemoteCLIP (MVRL/RemoteCLIP on
# HuggingFace) for significantly better domain alignment.

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Load physical CRII data
crii_df = pd.read_csv("data/india_crii_results.csv")

# Load CLIP scores
clip_df = pd.read_csv("data/clip_scores.csv")

# Create mapping (assuming image names like grid_0.jpg)
clip_df["grid_id"] = clip_df["image"].str.extract(r'(\d+)').astype(int)

# Merge
df = crii_df.merge(clip_df, on="grid_id")

# Normalize CLIP scores
scaler = MinMaxScaler()
df[["clip_flood", "clip_heat", "clip_veg", "clip_urban"]] = scaler.fit_transform(
    df[["flood_score", "heat_score", "vegetation_score", "urban_score"]]
)

# Combine semantic scores
df["clip_combined"] = (
    df["clip_flood"] +
    df["clip_heat"] +
    df["clip_veg"] +
    df["clip_urban"]
) / 4

# Final Hybrid CRII
df["hybrid_crii"] = (
    0.7 * df["crii"] +          # physical satellite signal
    0.3 * df["clip_combined"]   # semantic visual signal
).clip(0, 1)

# FIX: Unified classification thresholds (was 0.25/0.5/0.75 — now consistent
# with compute_crii_india.py which also uses 0.25/0.5/0.75)
def classify(val):
    if val < 0.25:
        return "Low"
    elif val < 0.50:
        return "Moderate"
    elif val < 0.75:
        return "High"
    else:
        return "Critical"

df["hybrid_risk"] = df["hybrid_crii"].apply(classify)

# Propagate uncertainty from physical CRII
# Hybrid uncertainty is slightly higher due to CLIP domain uncertainty
if "crii_uncertainty" in df.columns:
    df["hybrid_uncertainty"] = (df["crii_uncertainty"] + 0.02).round(3)

df.to_csv("data/hybrid_crii_results.csv", index=False)
print("Hybrid CRII computed ✅")
print("Risk distribution:")
print(df["hybrid_risk"].value_counts())
