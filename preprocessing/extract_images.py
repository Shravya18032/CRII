import ee
import pandas as pd
import requests
import os

ee.Initialize(project='mini-project-300606')

grid_df = pd.read_csv("data/bangalore_grid.csv")

# Use updated dataset
collection = ee.ImageCollection("COPERNICUS/S2_HARMONIZED") \
    .filterDate("2023-01-01", "2023-12-31") \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
    .select(['B4', 'B3', 'B2'])  # RGB

image = collection.mean()

# Visualization parameters (VERY IMPORTANT)
vis_params = {
    'min': 0,
    'max': 3000,
    'bands': ['B4', 'B3', 'B2']
}

os.makedirs("data/real_images", exist_ok=True)

for _, row in grid_df.iterrows():

    region = ee.Geometry.Rectangle([
        row["lon_min"],
        row["lat_min"],
        row["lon_max"],
        row["lat_max"]
    ])

    url = image.getThumbURL({
        'region': region,
        'dimensions': 256,
        'format': 'jpg',
        **vis_params   # FIX APPLIED HERE
    })

    img_data = requests.get(url).content

    filename = f"data/real_images/grid_{int(row['grid_id'])}.jpg"
    
    with open(filename, 'wb') as f:
        f.write(img_data)

print("Satellite images extracted")