import pandas as pd
import folium

# Load data
df = pd.read_csv("data/crii_results.csv")
grid_df = pd.read_csv("data/bangalore_grid.csv")

# Merge grid + results
df = df.merge(grid_df, on="grid_id")

# Create map centered on Bangalore
m = folium.Map(location=[13.0, 77.6], zoom_start=10)

# Color mapping
def get_color(risk):
    if risk == "Low":
        return "green"
    elif risk == "Moderate":
        return "yellow"
    elif risk == "High":
        return "orange"
    else:
        return "red"

# Add grid rectangles
for _, row in df.iterrows():
    folium.Rectangle(
        bounds=[
            [row["lat_min"], row["lon_min"]],
            [row["lat_max"], row["lon_max"]]
        ],
        color=get_color(row["risk_category"]),
        fill=True,
        fill_opacity=0.6,
        popup=f"CRII: {row['crii']:.2f} ({row['risk_category']})"
    ).add_to(m)

# Save map
m.save("visualization/crii_map.html")

print("Map generated successfully")