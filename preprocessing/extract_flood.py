import ee
import pandas as pd

ee.Initialize(project='mini-project-300606')

grid_df = pd.read_csv("data/bangalore_grid.csv")

# Sentinel-1 collection
s1_collection = ee.ImageCollection("COPERNICUS/S1_GRD") \
    .filterDate("2023-01-01", "2023-12-31") \
    .filter(ee.Filter.eq('instrumentMode', 'IW')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .select('VV')

# Take mean image
s1_image = s1_collection.mean()

results = []

for _, row in grid_df.iterrows():

    region = ee.Geometry.Rectangle([
        row["lon_min"],
        row["lat_min"],
        row["lon_max"],
        row["lat_max"]
    ])

    flood = s1_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=10
    )

    flood_value = flood.get("VV").getInfo()

    # Convert to flood susceptibility
    if flood_value is not None:
        flood_value = -flood_value  # invert (low → high risk)

    results.append({
        "grid_id": row["grid_id"],
        "flood": flood_value
    })

df = pd.DataFrame(results)
df.to_csv("data/grid_flood.csv", index=False)

print("Flood extraction completed")