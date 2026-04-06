import ee
import pandas as pd

ee.Initialize(project='mini-project-300606')

grid_df = pd.read_csv("data/bangalore_grid.csv")

# Load GHSL as ImageCollection
urban_collection = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_S")

# Take latest year (or mean)
urban_image = urban_collection.mean()

results = []

for _, row in grid_df.iterrows():

    region = ee.Geometry.Rectangle([
        row["lon_min"],
        row["lat_min"],
        row["lon_max"],
        row["lat_max"]
    ])

    urban = urban_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=100
    )

    # Correct band name
    urban_value = urban.get("built_surface").getInfo()

    if urban_value is not None:
        urban_value = urban_value / 100  # normalize

    results.append({
        "grid_id": row["grid_id"],
        "urban": urban_value
    })

df = pd.DataFrame(results)
df.to_csv("data/grid_urban.csv", index=False)

print("Urban extraction completed")