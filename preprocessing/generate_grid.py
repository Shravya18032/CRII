import pandas as pd
import numpy as np

lat_min, lat_max = 12.80, 13.20
lon_min, lon_max = 77.40, 77.80

grid_size = 0.05

latitudes = np.arange(lat_min, lat_max, grid_size)
longitudes = np.arange(lon_min, lon_max, grid_size)

grid_data = []

grid_id = 0

for lat in latitudes:
    for lon in longitudes:
        grid_data.append({
            "grid_id": grid_id,
            "lat_min": lat,
            "lat_max": lat + grid_size,
            "lon_min": lon,
            "lon_max": lon + grid_size
        })
        grid_id += 1

df = pd.DataFrame(grid_data)

df.to_csv("data/bangalore_grid.csv", index=False)

print("Grid generated:", len(df), "cells")