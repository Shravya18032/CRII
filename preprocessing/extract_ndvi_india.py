#preprocessing/extract_ndvi_india.py
import ee
import pandas as pd

ee.Initialize(project='mini-project-300606')

grid_df = pd.read_csv("data/india_grid.csv")

results = []

for i, row in grid_df.iterrows():
    print(f"Processing {i}")

    region = ee.Geometry.Rectangle([
        row["lon_min"],
        row["lat_min"],
        row["lon_max"],
        row["lat_max"]
    ])

    try:
        image = ee.ImageCollection("MODIS/061/MOD13Q1") \
            .select("NDVI") \
            .filterDate("2023-01-01", "2023-12-31") \
            .mean()

        value = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=500,
            maxPixels=1e13
        ).get("NDVI")

        if value:
            value = value.getInfo()
            value = value * 0.0001

        results.append({
            "grid_id": row["grid_id"],
            "ndvi": value
        })

    except:
        results.append({
            "grid_id": row["grid_id"],
            "ndvi": None
        })

df = pd.DataFrame(results)
df.to_csv("data/india_ndvi.csv", index=False)

print("NDVI extraction fixed ✅")