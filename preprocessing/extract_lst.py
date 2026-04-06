import ee
import pandas as pd

ee.Initialize(project='mini-project-300606')

grid_df = pd.read_csv("data/bangalore_grid.csv")

# MODIS LST dataset
lst_collection = ee.ImageCollection("MODIS/061/MOD11A2") \
                    .select("LST_Day_1km") \
                    .filterDate("2023-01-01", "2023-12-31")

results = []

for _, row in grid_df.iterrows():

    region = ee.Geometry.Rectangle([
        row["lon_min"],
        row["lat_min"],
        row["lon_max"],
        row["lat_max"]
    ])

    lst = lst_collection.mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000
    )

    lst_value = lst.get("LST_Day_1km").getInfo()

    if lst_value is not None:
        # Convert to Celsius
        lst_value = lst_value * 0.02 - 273.15

    results.append({
        "grid_id": row["grid_id"],
        "lst": lst_value
    })

df = pd.DataFrame(results)
df.to_csv("data/grid_lst.csv", index=False)

print("LST extraction completed")