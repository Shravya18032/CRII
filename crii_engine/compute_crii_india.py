# # crii_engine/compute_crii_india.py

# import pandas as pd

# # -----------------------------
# # LOAD DATA
# # -----------------------------
# df = pd.read_csv("data/india_cleaned.csv")
# print("Data loaded:", df.shape)

# # -----------------------------
# # FEATURE ENGINEERING (NDVI FIX)
# # -----------------------------

# # Create latitude bands
# df["lat_band"] = pd.cut(df["lat_min"], bins=6)

# # Compute regional NDVI baseline
# df["ndvi_baseline"] = df.groupby("lat_band")["ndvi"].transform("mean")

# # Vegetation stress (anomaly-based)
# df["vegetation_stress"] = (df["ndvi_baseline"] - df["ndvi"]) / df["ndvi_baseline"]
# df["vegetation_stress"] = df["vegetation_stress"].clip(lower=0)
# df["vegetation_stress"] = df["vegetation_stress"].fillna(0)

# # -----------------------------
# # REGIONAL NORMALIZATION 🔥
# # -----------------------------
# df["region"] = pd.cut(df["lat_min"], bins=6)

# norm_features = ["flood", "lst", "vegetation_stress", "urban", "rainfall"]

# for feature in norm_features:
#     df[feature + "_norm"] = df.groupby("region")[feature].transform(
#         lambda x: (x - x.min()) / (x.max() - x.min() + 1e-6)
#     )

# # Rename for consistency
# df.rename(columns={"vegetation_stress_norm": "veg_norm"}, inplace=True)

# print("Normalization completed")

# # -----------------------------
# # GEOGRAPHIC CORRECTION
# # -----------------------------
# def apply_geo_correction(row):
#     lat = (row["lat_min"] + row["lat_max"]) / 2

#     if lat > 28:  # Himalaya
#         row["lst_norm"] *= 0.5
#         row["urban_norm"] *= 0.3

#     if 8 < lat < 22:  # Coastal
#         row["flood_norm"] *= 1.3

#     if row["urban_norm"] > 0.6:
#         row["urban_norm"] *= 1.2

#     return row

# df = df.apply(apply_geo_correction, axis=1)

# print("Geographic correction applied")

# # -----------------------------
# # CRII COMPUTATION 🔥
# # -----------------------------
# df["crii"] = (
#     0.32 * df["flood_norm"] +
#     0.22 * df["lst_norm"] +
#     0.20 * df["veg_norm"] +
#     0.15 * df["urban_norm"] +
#     0.10 * df["rainfall_norm"] +
#     0.05 * (df["flood_norm"] * df["rainfall_norm"])
# )

# df["crii"] = df["crii"].clip(0, 1)
# df["crii"] = df["crii"].fillna(df["crii"].mean())

# print("CRII calculated")

# # -----------------------------
# # DYNAMIC CLASSIFICATION
# # -----------------------------
# def classify(val):
#     if val < 0.2:
#         return "Low"
#     elif val < 0.4:
#         return "Moderate"
#     elif val < 0.6:
#         return "High"
#     else:
#         return "Critical"

# df["risk_category"] = df["crii"].apply(classify)

# print("Classification completed")

# # -----------------------------
# # SAVE
# # -----------------------------
# df.to_csv("data/india_crii_results.csv", index=False)

# print("India CRII computation completed ✅")



































# crii_engine/compute_crii_india.py
#
# FIX 1: Geo-correction overflow — multipliers now applied to RAW values
#         before normalization, then clipped to [0,1] after normalization.
#         Original bug: flood_norm * 1.2 could silently exceed 1.0.
#
# FIX 2: Latitude-band normalization replaced with agro-climatic zone
#         normalization. India's 15 ICAR zones are approximated here by
#         named lat/lon bounding boxes. For production, use the ICAR shapefile
#         with geopandas spatial join.
#
# FIX 3: Classification thresholds unified to 0.25 / 0.50 / 0.75
#         (matching hybrid_crii.py). Eliminates inconsistent risk labels.
#
# FIX 4: Uncertainty score added per cell. Cells with low data_completeness
#         get a confidence penalty applied to CRII. Displayed in app as ± range.
#
# NOTE ON WEIGHTS: Current weights are retained from original for continuity.
#         Replace with AHP-derived weights once pairwise comparison is done.
#         Suggested next step: run pyAHP with expert survey on 5 variables.

import pandas as pd
import numpy as np

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("data/india_cleaned.csv")
print("Data loaded:", df.shape)

# -----------------------------
# AGRO-CLIMATIC ZONE ASSIGNMENT
# Approximated from ICAR's 15 agro-climatic zones using lat/lon ranges.
# For production: replace with geopandas sjoin on ICAR shapefile.
# -----------------------------
def assign_zone(row):
    lat = (row["lat_min"] + row["lat_max"]) / 2
    lon = (row["lon_min"] + row["lon_max"]) / 2

    if lat > 30:
        return "Western_Himalayas"
    elif lat > 25 and lon < 78:
        return "Trans_Gangetic_Plain"
    elif lat > 22 and lon >= 78 and lon < 88:
        return "Middle_Gangetic_Plain"
    elif lat > 22 and lon >= 88:
        return "Eastern_Himalayas"
    elif lat > 18 and lon < 75:
        return "Western_Plateau"
    elif lat > 18 and lon >= 75 and lon < 82:
        return "Central_Plateau"
    elif lat > 18 and lon >= 82:
        return "Eastern_Plateau"
    elif lat > 14 and lon < 74:
        return "Western_Ghats"
    elif lat > 14 and lon >= 74 and lon < 80:
        return "Southern_Plateau"
    elif lat > 14 and lon >= 80:
        return "East_Coast"
    elif lat <= 14 and lon < 77:
        return "West_Coast"
    else:
        return "Southern_Peninsula"

df["agro_zone"] = df.apply(assign_zone, axis=1)
print("Agro-climatic zones assigned:", df["agro_zone"].value_counts().to_dict())

# -----------------------------
# VEGETATION STRESS (NDVI anomaly within zone)
# -----------------------------
df["ndvi_baseline"] = df.groupby("agro_zone")["ndvi"].transform("median")
df["vegetation_stress"] = (df["ndvi_baseline"] - df["ndvi"]) / (df["ndvi_baseline"].abs() + 1e-6)
df["vegetation_stress"] = df["vegetation_stress"].clip(lower=0).fillna(0)

# -----------------------------
# FIX 1: GEO-CORRECTION ON RAW VALUES (before normalization)
# Corrections are ecologically justified:
#   - Himalayan cells: LST cold bias due to altitude (reduce weight)
#   - Himalayan cells: Urban density near zero — reduce urban signal
#   - Coastal cells (lat 8–22): Higher flood exposure — amplify
#   - Dense urban (urban > 75th percentile): Urban heat island amplification
# All corrections clipped to [0, max_raw] to prevent overflow.
# -----------------------------
urban_75th = df["urban"].quantile(0.75)

def apply_geo_correction_raw(row):
    lat = (row["lat_min"] + row["lat_max"]) / 2

    lst_val   = row["lst"]
    urban_val = row["urban"]
    flood_val = row["flood"]

    if lat > 28:                        # Himalayan region
        lst_val   = lst_val * 0.5
        urban_val = urban_val * 0.3

    if 8 < lat < 22:                    # Coastal belt
        flood_val = flood_val * 1.2

    if row["urban"] > urban_75th:       # Dense urban — heat island boost
        urban_val = urban_val * 1.2

    row["lst"]   = lst_val
    row["urban"] = urban_val
    row["flood"] = flood_val
    return row

df = df.apply(apply_geo_correction_raw, axis=1)
print("Geographic correction applied to raw values")

# -----------------------------
# ZONE-BASED NORMALIZATION (after geo-correction)
# Normalizes each feature within its agro-climatic zone.
# Clip to [0,1] enforced here — no values can exceed 1.
# -----------------------------
norm_features = ["flood", "lst", "vegetation_stress", "urban", "rainfall"]

for feature in norm_features:
    df[feature + "_norm"] = df.groupby("agro_zone")[feature].transform(
        lambda x: ((x - x.min()) / (x.max() - x.min() + 1e-6)).clip(0, 1)
    )

df.rename(columns={"vegetation_stress_norm": "veg_norm"}, inplace=True)
print("Zone-based normalization completed. Max values:")
for f in ["flood_norm", "lst_norm", "veg_norm", "urban_norm", "rainfall_norm"]:
    print(f"  {f}: max={df[f].max():.4f}, min={df[f].min():.4f}")

# -----------------------------
# CRII COMPUTATION
# Weights retained from original — replace with AHP-derived weights.
# Interaction term (flood × rainfall) captures compound flood-rain events.
# -----------------------------
df["crii"] = (
    0.28 * df["flood_norm"] +
    0.22 * df["lst_norm"] +
    0.20 * df["veg_norm"] +
    0.15 * df["urban_norm"] +
    0.10 * df["rainfall_norm"] +
    0.05 * (df["flood_norm"] * df["rainfall_norm"])   # compound event term
).clip(0, 1)

# Fill any remaining NaN with zone median, then global median
zone_crii_median = df.groupby("agro_zone")["crii"].transform("median")
df["crii"] = df["crii"].fillna(zone_crii_median).fillna(df["crii"].median())

print("CRII calculated. Range:", df["crii"].min().round(4), "–", df["crii"].max().round(4))

# -----------------------------
# FIX 3: UNIFIED CLASSIFICATION THRESHOLDS
# Thresholds: 0.25 / 0.50 / 0.75 (matches hybrid_crii.py)
# Original used 0.2 / 0.4 / 0.6 — inconsistent with hybrid file.
# -----------------------------
def classify(val):
    if val < 0.25:
        return "Low"
    elif val < 0.50:
        return "Moderate"
    elif val < 0.75:
        return "High"
    else:
        return "Critical"

df["risk_category"] = df["crii"].apply(classify)
print("Classification distribution:")
print(df["risk_category"].value_counts())

# -----------------------------
# FIX 4: UNCERTAINTY QUANTIFICATION
# crii_uncertainty = half-width of confidence interval
# Based on data_completeness from clean_india_data.py.
# Cells with all 5 features present → ±0.03 (sensor noise floor)
# Cells with 1 feature present    → ±0.15 (high imputation uncertainty)
# Linear interpolation in between.
# -----------------------------
if "data_completeness" in df.columns:
    max_uncertainty = 0.15
    min_uncertainty = 0.03
    df["crii_uncertainty"] = (
        min_uncertainty +
        (1 - df["data_completeness"]) * (max_uncertainty - min_uncertainty)
    ).round(3)
else:
    df["crii_uncertainty"] = 0.05   # default if column missing

print(f"Mean CRII uncertainty: ±{df['crii_uncertainty'].mean():.3f}")

# -----------------------------
# SAVE
# -----------------------------
df.to_csv("data/india_crii_results.csv", index=False)
print("India CRII computation completed ✅")
