import ee
import pandas as pd

# Initialize Earth Engine
ee.Initialize(project='mini-project-300606')

# Load grid CSV
grid_df = pd.read_csv("data/bangalore_grid.csv")

# MODIS NDVI dataset
ndvi_collection = ee.ImageCollection("MODIS/061/MOD13A2") \
                    .select("NDVI") \
                    .filterDate("2023-01-01", "2023-12-31")

results = []

for _, row in grid_df.iterrows():

    region = ee.Geometry.Rectangle([
        row["lon_min"],
        row["lat_min"],
        row["lon_max"],
        row["lat_max"]
    ])

    ndvi = ndvi_collection.mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000
    )

    ndvi_value = ndvi.get("NDVI").getInfo()

    if ndvi_value is not None:
        ndvi_value = ndvi_value * 0.0001

    results.append({
        "grid_id": row["grid_id"],
        "ndvi": ndvi_value
    })

# Save results
ndvi_df = pd.DataFrame(results)
ndvi_df.to_csv("data/grid_ndvi.csv", index=False)

print("NDVI extraction completed")