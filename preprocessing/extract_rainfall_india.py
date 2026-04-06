#preprocessing/extract_rainfall_india.py
import ee
import pandas as pd

ee.Initialize(project='mini-project-300606')

# Load grid
grid_df = pd.read_csv("data/india_grid.csv")

# Convert to FeatureCollection
features = []

for _, row in grid_df.iterrows():
    rect = ee.Geometry.Rectangle([
        row["lon_min"],
        row["lat_min"],
        row["lon_max"],
        row["lat_max"]
    ])

    features.append(
        ee.Feature(rect, {"grid_id": int(row["grid_id"])})
    )

fc = ee.FeatureCollection(features)

# ERA5 rainfall dataset
collection = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") \
    .select("total_precipitation_sum") \
    .filterDate("2023-01-01", "2023-12-31")

image = collection.mean()

# Compute rainfall per grid
result = image.reduceRegions(
    collection=fc,
    reducer=ee.Reducer.mean(),
    scale=10000   # coarse but faster
)

# Convert to pandas
data = result.getInfo()["features"]

rows = []
for item in data:
    props = item["properties"]

    rows.append({
        "grid_id": props["grid_id"],
        "rainfall": props.get("mean")
    })

df = pd.DataFrame(rows)
df.to_csv("data/india_rainfall.csv", index=False)

print("India Rainfall extraction completed ✅")