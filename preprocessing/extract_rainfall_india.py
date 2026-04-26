# #preprocessing/extract_rainfall_india.py
# import ee
# import pandas as pd

# ee.Initialize(project='mini-project-300606')

# # Load grid
# grid_df = pd.read_csv("data/india_grid.csv")

# # Convert to FeatureCollection
# features = []

# for _, row in grid_df.iterrows():
#     rect = ee.Geometry.Rectangle([
#         row["lon_min"],
#         row["lat_min"],
#         row["lon_max"],
#         row["lat_max"]
#     ])

#     features.append(
#         ee.Feature(rect, {"grid_id": int(row["grid_id"])})
#     )

# fc = ee.FeatureCollection(features)

# # ERA5 rainfall dataset
# collection = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") \
#     .select("total_precipitation_sum") \
#     .filterDate("2023-01-01", "2023-12-31")

# image = collection.mean()

# # Compute rainfall per grid
# result = image.reduceRegions(
#     collection=fc,
#     reducer=ee.Reducer.mean(),
#     scale=10000   # coarse but faster
# )

# # Convert to pandas
# data = result.getInfo()["features"]

# rows = []
# for item in data:
#     props = item["properties"]

#     rows.append({
#         "grid_id": props["grid_id"],
#         "rainfall": props.get("mean")
#     })

# df = pd.DataFrame(rows)
# df.to_csv("data/india_rainfall.csv", index=False)

# print("India Rainfall extraction completed ✅")









































# preprocessing/extract_rainfall_india.py
#
# UPGRADE — Step 1 of Week 1
# Replaced: ERA5 annual mean rainfall (coarse, no drought context)
# With:     CHIRPS SPI-3 (Standardized Precipitation Index, 3-month rolling)
#
# Why SPI-3?
#   - Official IMD standard for drought declaration
#   - Captures relative rainfall anomaly vs historical baseline (1981–2023)
#   - SPI < -1 = moderate drought, SPI < -2 = severe drought
#   - CHIRPS resolution: 5km (vs ERA5's 10km) — more precise for India
#
# How SPI-3 is computed here:
#   1. Load CHIRPS daily rainfall for 2023 (target year)
#   2. Compute monthly totals for Oct, Nov, Dec 2022 + Jan–Dec 2023
#      (we need 3-month windows)
#   3. Load CHIRPS historical baseline 2000–2022 (same months)
#   4. For each grid cell, compute mean and std of historical 3-month
#      totals for the same calendar quarter
#   5. SPI = (observed_3month - historical_mean) / historical_std
#   6. We output ANNUAL MEAN SPI across all 4 quarters of 2023
#      to get a yearly drought signal per cell
#
# Output columns:
#   grid_id, spi3_mean, spi3_min, drought_flag
#   drought_flag = 1 if spi3_min < -1 (at least one drought quarter)
#
# Note: GEE computation is heavy — batching at 30 cells avoids timeouts.
# Expected runtime: 30–50 minutes for full India grid.

import ee
import pandas as pd
import numpy as np

ee.Initialize(project='mini-project-300606')

grid_df = pd.read_csv("data/india_grid.csv")

# ── CHIRPS DATASET ───────────────────────────────────────────────
# UCSB-CHG/CHIRPS/DAILY — 5km resolution, 1981–present
# Units: mm/day
CHIRPS = "UCSB-CHG/CHIRPS/DAILY"

# ── DEFINE QUARTERLY WINDOWS FOR 2023 ───────────────────────────
# We compute SPI for 4 rolling 3-month windows across 2023:
# Q1: Nov–Jan (NEM / winter), Q2: Feb–Apr (pre-monsoon)
# Q3: May–Jul (early monsoon), Q4: Aug–Oct (peak/post monsoon)
QUARTERS_2023 = [
    ("Q1_NovJanFeb", "2022-11-01", "2023-01-31"),
    ("Q2_FebApr",    "2023-02-01", "2023-04-30"),
    ("Q3_MayJul",    "2023-05-01", "2023-07-31"),
    ("Q4_AugOct",    "2023-08-01", "2023-10-31"),
]

# Historical baseline: same quarters, 2000–2022 (23 years)
BASELINE_YEARS = list(range(2000, 2023))

# ── HELPER: get 3-month total image for a date range ────────────
def get_quarterly_total(start, end):
    return (
        ee.ImageCollection(CHIRPS)
        .filterDate(start, end)
        .sum()                    # total mm over the 3-month window
        .rename("precip")
    )

# ── BUILD HISTORICAL BASELINE STATS ─────────────────────────────
# For each quarter definition, get mean and stddev across 23 years
# Returns a dict: quarter_name → {"mean": ee.Image, "std": ee.Image}
def build_baseline(quarter_name, start_mmdd, end_mmdd):
    """
    Compute historical mean + std for a quarter across BASELINE_YEARS.
    start_mmdd / end_mmdd: e.g. "11-01", "01-31"
    """
    images = []
    for yr in BASELINE_YEARS:
        # Handle cross-year quarters (Nov-Jan)
        if start_mmdd.startswith("11") or start_mmdd.startswith("12"):
            s = f"{yr}-{start_mmdd}"
            e = f"{yr+1}-{end_mmdd}"
        else:
            s = f"{yr}-{start_mmdd}"
            e = f"{yr}-{end_mmdd}"
        img = get_quarterly_total(s, e)
        images.append(img)

    col      = ee.ImageCollection(images)
    baseline_mean = col.mean().rename("hist_mean")
    baseline_std  = col.reduce(ee.Reducer.stdDev()).rename("hist_std")
    return baseline_mean, baseline_std

# ── BATCH PROCESSING ─────────────────────────────────────────────
BATCH_SIZE = 30      # smaller batches for heavy SPI computation
all_rows   = []

print(f"Computing SPI-3 for {len(grid_df)} grid cells across 4 quarters...")
print("This will take 30–50 minutes for full India. Grab a coffee ☕\n")

for q_name, q_start, q_end in QUARTERS_2023:
    print(f"─── Quarter: {q_name} ({q_start} → {q_end}) ───")

    # Observed 3-month total for 2023
    observed = get_quarterly_total(q_start, q_end)

    # Historical baseline for same quarter
    start_mmdd = q_start[5:]    # "MM-DD" portion
    end_mmdd   = q_end[5:]
    hist_mean, hist_std = build_baseline(q_name, start_mmdd, end_mmdd)

    # SPI image: (observed - mean) / std
    # Clip std to avoid division near zero in arid regions
    hist_std_safe = hist_std.max(ee.Image.constant(1.0))
    spi_image = (observed.subtract(hist_mean)).divide(hist_std_safe).rename("spi3")

    for i in range(0, len(grid_df), BATCH_SIZE):
        print(f"  Batch {i}–{i+BATCH_SIZE}...", end=" ", flush=True)

        batch    = grid_df.iloc[i:i + BATCH_SIZE]
        features = []

        for _, row in batch.iterrows():
            rect = ee.Geometry.Rectangle([
                row["lon_min"], row["lat_min"],
                row["lon_max"], row["lat_max"]
            ])
            features.append(ee.Feature(rect, {"grid_id": int(row["grid_id"])}))

        fc = ee.FeatureCollection(features)

        result = spi_image.reduceRegions(
            collection=fc,
            reducer=ee.Reducer.mean(),
            scale=5000          # CHIRPS native resolution ~5km
        )

        try:
            data = result.getInfo()["features"]
            for item in data:
                props = item["properties"]
                all_rows.append({
                    "grid_id":  props["grid_id"],
                    "quarter":  q_name,
                    "spi3":     props.get("mean"),
                })
            print(f"✓ {len(data)} cells")

        except Exception as e:
            print(f"✗ failed: {e}")
            for _, row in batch.iterrows():
                all_rows.append({
                    "grid_id": int(row["grid_id"]),
                    "quarter": q_name,
                    "spi3":    None,
                })

# ── AGGREGATE QUARTERS INTO ANNUAL SIGNAL ───────────────────────
print("\nAggregating quarterly SPI into annual drought signal...")

df_long = pd.DataFrame(all_rows)

# Pivot: one row per grid_id, one column per quarter
df_wide = df_long.pivot_table(
    index="grid_id",
    columns="quarter",
    values="spi3",
    aggfunc="mean"
).reset_index()

# Annual SPI stats
quarter_cols = [q[0] for q in QUARTERS_2023]
available_q  = [c for c in quarter_cols if c in df_wide.columns]

df_wide["spi3_mean"] = df_wide[available_q].mean(axis=1)
df_wide["spi3_min"]  = df_wide[available_q].min(axis=1)

# Drought flag: at least one quarter was moderately dry (SPI < -1)
df_wide["drought_flag"] = (df_wide["spi3_min"] < -1).astype(int)

# ── CONVERT SPI TO RISK SCORE [0, 1] ─────────────────────────────
# SPI ranges roughly -3 to +3.
# We want: negative SPI (drought) → higher risk score
# Map: SPI +3 → risk 0.0 (very wet, low drought risk)
#      SPI  0 → risk 0.5 (normal)
#      SPI -3 → risk 1.0 (severe drought, high risk)
# Formula: rainfall_risk = clip((-spi3_mean + 3) / 6, 0, 1)
df_wide["rainfall"] = ((-df_wide["spi3_mean"] + 3) / 6).clip(0, 1)

# Fill any remaining nulls with zone median
df_wide["rainfall"] = df_wide["rainfall"].fillna(df_wide["rainfall"].median())

# ── SAVE ─────────────────────────────────────────────────────────
# Save both the detailed quarterly file and the simple rainfall file
# that clean_india_data.py expects

df_wide[["grid_id", "spi3_mean", "spi3_min", "drought_flag", "rainfall"]]\
    .to_csv("data/india_spi3_detail.csv", index=False)

# Backward-compatible output for clean_india_data.py
df_wide[["grid_id", "rainfall"]].to_csv("data/india_rainfall.csv", index=False)

print("\n─── SPI-3 Extraction Complete ✅ ───")
print(f"Total cells processed: {len(df_wide)}")
print(f"Cells with valid SPI: {df_wide['spi3_mean'].notna().sum()}")
print(f"Drought-flagged cells (SPI < -1 in any quarter): {df_wide['drought_flag'].sum()}")
print(f"\nSPI-3 distribution:")
print(df_wide["spi3_mean"].describe().round(3))
print(f"\nFiles saved:")
print("  data/india_rainfall.csv      ← drop-in replacement for clean_india_data.py")
print("  data/india_spi3_detail.csv   ← quarterly breakdown for analysis")