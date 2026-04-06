#preprocessing/extract_flood_india.py
import ee
import pandas as pd

ee.Initialize(project='mini-project-300606')

# Load grid
grid_df = pd.read_csv("data/india_grid.csv")

# Split into batches
batch_size = 50   # IMPORTANT
all_rows = []

# Sentinel-1 dataset
collection = ee.ImageCollection("COPERNICUS/S1_GRD") \
    .filterDate("2023-01-01", "2023-12-31") \
    .filter(ee.Filter.eq('instrumentMode', 'IW')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .select('VV')

image = collection.mean()

for i in range(0, len(grid_df), batch_size):
    print(f"Processing batch {i} to {i+batch_size}")

    batch = grid_df.iloc[i:i+batch_size]

    features = []

    for _, row in batch.iterrows():
        rect = ee.Geometry.Rectangle([
            row["lon_min"],
            row["lat_min"],
            row["lon_max"],
            row["lat_max"]
        ])

        feature = ee.Feature(rect, {"grid_id": int(row["grid_id"])})
        features.append(feature)

    fc = ee.FeatureCollection(features)

    result = image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=100
    )

    data = result.getInfo()["features"]

    for item in data:
        props = item["properties"]

        val = props.get("VV")

        if val is not None:
            val = -val

        all_rows.append({
            "grid_id": props["grid_id"],
            "flood": val
        })

# Save final
df = pd.DataFrame(all_rows)
df.to_csv("data/india_flood.csv", index=False)

print("India Flood extraction completed")