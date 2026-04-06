#preprocessing/extract_urban_india.py
import ee
import pandas as pd

ee.Initialize(project='mini-project-300606')

# Load grid
grid_df = pd.read_csv("data/india_grid.csv")

# Convert grid to FeatureCollection
features = []

for _, row in grid_df.iterrows():
    rect = ee.Geometry.Rectangle([
        row["lon_min"],
        row["lat_min"],
        row["lon_max"],
        row["lat_max"]
    ])

    feature = ee.Feature(rect, {"grid_id": int(row["grid_id"])})
    features.append(feature)

fc = ee.FeatureCollection(features)

# GHSL dataset (ImageCollection)
collection = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_S")

image = collection.mean()

# Compute urban per grid
result = image.reduceRegions(
    collection=fc,
    reducer=ee.Reducer.mean(),
    scale=100
)

# Convert to pandas
data = result.getInfo()["features"]

rows = []
for item in data:
    props = item["properties"]

    val = props.get("built_surface")

    if val is not None:
        val = val / 100  # normalize

    rows.append({
        "grid_id": props["grid_id"],
        "urban": val
    })

df = pd.DataFrame(rows)
df.to_csv("data/india_urban.csv", index=False)

print("India Urban extraction completed")