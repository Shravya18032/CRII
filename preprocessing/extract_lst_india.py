#preprocessing/extract_lst_india.py
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

# LST dataset (MODIS)
collection = ee.ImageCollection("MODIS/061/MOD11A2") \
    .select("LST_Day_1km") \
    .filterDate("2023-01-01", "2023-12-31")

image = collection.mean()

# Convert to Celsius
image = image.multiply(0.02).subtract(273.15)

# Compute LST per grid
result = image.reduceRegions(
    collection=fc,
    reducer=ee.Reducer.mean(),
    scale=1000
)

# Convert to pandas
data = result.getInfo()["features"]

rows = []
for item in data:
    props = item["properties"]

    rows.append({
        "grid_id": props["grid_id"],
        "lst": props.get("mean")
    })

df = pd.DataFrame(rows)
df.to_csv("data/india_lst.csv", index=False)

print("India LST extraction completed")