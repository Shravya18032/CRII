#preprocessing/generate_grid_india.py
import pandas as pd

# India bounding box
lat_min, lat_max = 6, 38
lon_min, lon_max = 68, 98

# Larger grid (IMPORTANT for performance)
grid_size = 0.5   # ~50 km

grid_data = []
grid_id = 0

lat = lat_min
while lat < lat_max:
    lon = lon_min
    while lon < lon_max:
        grid_data.append({
            "grid_id": grid_id,
            "lat_min": lat,
            "lat_max": lat + grid_size,
            "lon_min": lon,
            "lon_max": lon + grid_size
        })
        grid_id += 1
        lon += grid_size
    lat += grid_size

df = pd.DataFrame(grid_data)
df.to_csv("data/india_grid.csv", index=False)

print("India grid created:", len(df), "cells")