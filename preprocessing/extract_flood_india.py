# #preprocessing/extract_flood_india.py
# import ee
# import pandas as pd

# ee.Initialize(project='mini-project-300606')

# # Load grid
# grid_df = pd.read_csv("data/india_grid.csv")

# # Split into batches
# batch_size = 50   # IMPORTANT
# all_rows = []

# # JRC Global Surface Water
# image = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("seasonality")

# for i in range(0, len(grid_df), batch_size):
#     print(f"Processing batch {i} to {i+batch_size}")

#     batch = grid_df.iloc[i:i+batch_size]

#     features = []

#     for _, row in batch.iterrows():
#         rect = ee.Geometry.Rectangle([
#             row["lon_min"],
#             row["lat_min"],
#             row["lon_max"],
#             row["lat_max"]
#         ])

#         feature = ee.Feature(rect, {"grid_id": int(row["grid_id"])})
#         features.append(feature)

#     fc = ee.FeatureCollection(features)

#     result = image.reduceRegions(
#         collection=fc,
#         reducer=ee.Reducer.mean(),
#         scale=100
#     )

#     data = result.getInfo()["features"]

#     for item in data:
#         props = item["properties"]

#         val = props.get("seasonality")

#         if val is not None:
#             val = val / 12

#         all_rows.append({
#             "grid_id": props["grid_id"],
#             "flood": val
#         })

# # Save final
# df = pd.DataFrame(all_rows)
# df.to_csv("data/india_flood.csv", index=False)

# print("India Flood extraction completed")





























# preprocessing/extract_flood_india.py
#
# FIX APPLIED: Replaced Sentinel-1 annual mean VV backscatter with JRC Global
# Surface Water 'seasonality' band. VV backscatter is a surface roughness signal,
# NOT a flood signal. JRC GSW seasonality = number of months/year water is present
# — purpose-built, peer-reviewed, freely available on GEE.
# Dataset: JRC/GSW1_4/GlobalSurfaceWater
# Reference: Pekel et al. (2016), Nature, doi:10.1038/nature20584
#
# ALSO FIXED: Batch errors now logged explicitly instead of silently dropped.

import ee
import pandas as pd

ee.Initialize(project='mini-project-300606')

# Load grid
grid_df = pd.read_csv("data/india_grid.csv")

batch_size = 50
all_rows = []

# ---------------------------------------------------------
# JRC Global Surface Water — seasonality band
# Range: 0–12 (months/year water is present)
# Higher value = more persistent surface water = higher flood risk
# ---------------------------------------------------------
jrc_image = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("seasonality")

for i in range(0, len(grid_df), batch_size):
    print(f"Processing batch {i} to {i + batch_size}...")

    batch = grid_df.iloc[i:i + batch_size]
    features = []

    for _, row in batch.iterrows():
        rect = ee.Geometry.Rectangle([
            row["lon_min"],
            row["lat_min"],
            row["lon_max"],
            row["lat_max"]
        ])
        features.append(ee.Feature(rect, {"grid_id": int(row["grid_id"])}))

    fc = ee.FeatureCollection(features)

    result = jrc_image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=30        # JRC native resolution is 30m
    )

    try:
        data = result.getInfo()["features"]
        for item in data:
            props = item["properties"]
            val = props.get("mean")

            # Normalize to [0, 1]: seasonality ranges 0–12 months
            if val is not None:
                val = val / 12.0

            all_rows.append({
                "grid_id": props["grid_id"],
                "flood": val
            })

    except Exception as e:
        print(f"  Batch {i} failed: {e}")
        # On batch failure, append None for affected cells (not silently dropped)
        for _, row in batch.iterrows():
            all_rows.append({"grid_id": int(row["grid_id"]), "flood": None})

df = pd.DataFrame(all_rows)
df.to_csv("data/india_flood.csv", index=False)

print(f"India Flood extraction completed. {df['flood'].notna().sum()} / {len(df)} cells valid.")