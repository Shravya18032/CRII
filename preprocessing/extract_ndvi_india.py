# #preprocessing/extract_ndvi_india.py
# import ee
# import pandas as pd

# ee.Initialize(project='mini-project-300606')

# grid_df = pd.read_csv("data/india_grid.csv")

# results = []

# for i, row in grid_df.iterrows():
#     print(f"Processing {i}")

#     region = ee.Geometry.Rectangle([
#         row["lon_min"],
#         row["lat_min"],
#         row["lon_max"],
#         row["lat_max"]
#     ])

#     try:
#         image = ee.ImageCollection("MODIS/061/MOD13Q1") \
#             .select("NDVI") \
#             .filterDate("2023-01-01", "2023-12-31") \
#             .mean()

#         value = image.reduceRegion(
#             reducer=ee.Reducer.mean(),
#             geometry=region,
#             scale=500,
#             maxPixels=1e13
#         ).get("NDVI")

#         if value:
#             value = value.getInfo()
#             value = value * 0.0001

#         results.append({
#             "grid_id": row["grid_id"],
#             "ndvi": value
#         })

#     except:
#         results.append({
#             "grid_id": row["grid_id"],
#             "ndvi": None
#         })

# df = pd.DataFrame(results)
# df.to_csv("data/india_ndvi.csv", index=False)

# print("NDVI extraction fixed ✅")






























# preprocessing/extract_ndvi_india.py
#
# FIX APPLIED: Replaced row-by-row getInfo() loop with batched reduceRegions().
# Original code made ~3,840 separate GEE API calls (one per grid cell).
# This fix makes ~77 calls (50 cells per batch) — runtime: hours → minutes.
#
# FIX APPLIED: Replaced bare except: with except Exception as e — errors are now
# logged with the actual message so API quota/auth failures are visible.

import ee
import pandas as pd

ee.Initialize(project='mini-project-300606')

grid_df = pd.read_csv("data/india_grid.csv")

batch_size = 50
all_rows = []

# MODIS NDVI — scale factor 0.0001 applied after extraction
ndvi_image = (
    ee.ImageCollection("MODIS/061/MOD13Q1")
    .select("NDVI")
    .filterDate("2023-01-01", "2023-12-31")
    .mean()
    .multiply(0.0001)       # apply scale factor once, on the image (efficient)
)

for i in range(0, len(grid_df), batch_size):
    print(f"Processing NDVI batch {i} to {i + batch_size}...")

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

    result = ndvi_image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=500           # MODIS MOD13Q1 native resolution
    )

    try:
        data = result.getInfo()["features"]
        for item in data:
            props = item["properties"]
            all_rows.append({
                "grid_id": props["grid_id"],
                "ndvi": props.get("mean")   # already scaled by 0.0001
            })

    except Exception as e:
        print(f"  NDVI batch {i} failed: {e}")
        for _, row in batch.iterrows():
            all_rows.append({"grid_id": int(row["grid_id"]), "ndvi": None})

df = pd.DataFrame(all_rows)
df.to_csv("data/india_ndvi.csv", index=False)

print(f"NDVI extraction completed. {df['ndvi'].notna().sum()} / {len(df)} cells valid.")