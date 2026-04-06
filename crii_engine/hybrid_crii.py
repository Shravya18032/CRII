import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Load physical CRII data
crii_df = pd.read_csv("data/crii_results.csv")

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
    0.7 * df["crii"] +      # physical
    0.3 * df["clip_combined"]  # semantic
)

# Classification
def classify(val):
    if val < 0.25:
        return "Low"
    elif val < 0.5:
        return "Moderate"
    elif val < 0.75:
        return "High"
    else:
        return "Critical"

df["hybrid_risk"] = df["hybrid_crii"].apply(classify)

# Save
df.to_csv("data/hybrid_crii_results.csv", index=False)

print("Hybrid CRII computed")