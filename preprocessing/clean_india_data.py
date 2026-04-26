# import pandas as pd

# # Load datasets
# ndvi = pd.read_csv("data/india_ndvi.csv")
# lst = pd.read_csv("data/india_lst.csv")
# urban = pd.read_csv("data/india_urban.csv")
# flood = pd.read_csv("data/india_flood.csv")
# rainfall = pd.read_csv("data/india_rainfall.csv")   # NEW
# grid = pd.read_csv("data/india_grid.csv")

# # Convert to numeric
# for df in [ndvi, lst, urban, flood, rainfall]:
#     for col in df.columns:
#         if col != "grid_id":
#             df[col] = pd.to_numeric(df[col], errors="coerce")

# # Merge ALL (outer join)
# df = grid.merge(ndvi, on="grid_id", how="left") \
#          .merge(lst, on="grid_id", how="left") \
#          .merge(urban, on="grid_id", how="left") \
#          .merge(flood, on="grid_id", how="left") \
#          .merge(rainfall, on="grid_id", how="left")

# print("After merge:")
# print(df.isna().sum())

# # -----------------------------
# # SMART FILLING
# # -----------------------------

# df["ndvi"] = df["ndvi"].fillna(df["ndvi"].mean())
# df["lst"] = df["lst"].fillna(df["lst"].mean())
# df["urban"] = df["urban"].fillna(df["urban"].mean())
# df["flood"] = df["flood"].fillna(df["flood"].mean())
# df["rainfall"] = df["rainfall"].fillna(df["rainfall"].mean())  # NEW

# # Final safety
# df = df.fillna(0)

# print("After cleaning:")
# print(df.isna().sum())

# # Save
# df.to_csv("data/india_cleaned.csv", index=False)

# print("Data cleaning with rainfall completed ✅")





















# clean_india_data.py
#
# FIX APPLIED: Replaced global mean NaN fill with spatial neighbor median.
# Original code: df["ndvi"].fillna(df["ndvi"].mean())
# Problem: A Thar Desert cell with missing NDVI inherited the national average —
# which includes lush Kerala values — producing a completely wrong score.
#
# Fix: For each missing cell, fill with the median value of its 8 spatial
# neighbors (cells sharing a border or corner). If all neighbors are also null,
# fall back to the agro-climatic zone median, then global median as last resort.
# This is spatially coherent and scientifically defensible.
#
# FIX APPLIED: Added data_completeness score per cell (used later for
# uncertainty quantification in compute_crii_india.py).

import pandas as pd
import numpy as np

# Load datasets
ndvi     = pd.read_csv("data/india_ndvi.csv")
lst      = pd.read_csv("data/india_lst.csv")
urban    = pd.read_csv("data/india_urban.csv")
flood    = pd.read_csv("data/india_flood.csv")
rainfall = pd.read_csv("data/india_rainfall.csv")
grid     = pd.read_csv("data/india_grid.csv")

# Convert to numeric
for df_temp in [ndvi, lst, urban, flood, rainfall]:
    for col in df_temp.columns:
        if col != "grid_id":
            df_temp[col] = pd.to_numeric(df_temp[col], errors="coerce")

# Merge all (left join on grid)
df = grid \
    .merge(ndvi,     on="grid_id", how="left") \
    .merge(lst,      on="grid_id", how="left") \
    .merge(urban,    on="grid_id", how="left") \
    .merge(flood,    on="grid_id", how="left") \
    .merge(rainfall, on="grid_id", how="left")

print("After merge — missing values:")
print(df.isna().sum())

# ---------------------------------------------------------
# SPATIAL NEIGHBOR MEDIAN FILL
# For each missing cell, use the median of its 8 spatial
# neighbors. Neighbors are identified by proximity in lat/lon.
# ---------------------------------------------------------
FEATURES = ["ndvi", "lst", "urban", "flood", "rainfall"]

grid_size = 0.5     # must match generate_grid_india.py

def spatial_neighbor_fill(df, feature, grid_size=0.5, tolerance=0.01):
    """Fill NaN values using the median of 8 spatial neighbors."""
    missing_mask = df[feature].isna()
    n_missing = missing_mask.sum()
    if n_missing == 0:
        return df

    print(f"  Filling {n_missing} missing '{feature}' values via spatial neighbors...")

    df = df.copy()
    lat_mid = (df["lat_min"] + df["lat_max"]) / 2
    lon_mid = (df["lon_min"] + df["lon_max"]) / 2

    for idx in df[missing_mask].index:
        cell_lat = lat_mid[idx]
        cell_lon = lon_mid[idx]

        # Find 8-neighbors: cells within 1 grid step in lat and lon
        neighbor_mask = (
            (lat_mid >= cell_lat - grid_size - tolerance) &
            (lat_mid <= cell_lat + grid_size + tolerance) &
            (lon_mid >= cell_lon - grid_size - tolerance) &
            (lon_mid <= cell_lon + grid_size + tolerance) &
            (df.index != idx)
        )

        neighbor_vals = df.loc[neighbor_mask & df[feature].notna(), feature]

        if len(neighbor_vals) > 0:
            df.at[idx, feature] = neighbor_vals.median()

    return df

for feature in FEATURES:
    df = spatial_neighbor_fill(df, feature, grid_size=grid_size)

# ---------------------------------------------------------
# FALLBACK: zone median → global median
# For cells still null after spatial fill (e.g., isolated ocean/border cells)
# ---------------------------------------------------------

# Assign coarse zone by latitude for fallback only
df["_zone"] = pd.cut(df["lat_min"], bins=6)

for feature in FEATURES:
    # Zone median fallback
    zone_medians = df.groupby("_zone")[feature].transform("median")
    df[feature] = df[feature].fillna(zone_medians)

    # Global median as final fallback
    df[feature] = df[feature].fillna(df[feature].median())

df.drop(columns=["_zone"], inplace=True)

# ---------------------------------------------------------
# DATA COMPLETENESS SCORE (0–1)
# Fraction of features that were originally non-null.
# Used downstream for uncertainty quantification.
# ---------------------------------------------------------
original_merges = grid \
    .merge(ndvi,     on="grid_id", how="left") \
    .merge(lst,      on="grid_id", how="left") \
    .merge(urban,    on="grid_id", how="left") \
    .merge(flood,    on="grid_id", how="left") \
    .merge(rainfall, on="grid_id", how="left")

df["data_completeness"] = original_merges[FEATURES].notna().mean(axis=1)

print("\nAfter spatial fill — missing values:")
print(df[FEATURES].isna().sum())
print(f"\nMean data completeness: {df['data_completeness'].mean():.2f}")

df.to_csv("data/india_cleaned.csv", index=False)
print("\nData cleaning completed ✅")
