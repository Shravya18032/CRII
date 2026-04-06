# import pandas as pd
# import folium

# # Load data
# df = pd.read_csv("data/india_crii_results.csv")

# # Create base map (center of India)
# m = folium.Map(location=[22.5, 80], zoom_start=5)

# # Color function
# def get_color(risk):
#     if risk == "Low":
#         return "green"
#     elif risk == "Moderate":
#         return "orange"
#     elif risk == "High":
#         return "red"
#     else:
#         return "darkred"

# # Add grid rectangles
# for _, row in df.iterrows():

#     try:
#         bounds = [
#             [row["lat_min"], row["lon_min"]],
#             [row["lat_max"], row["lon_max"]]
#         ]

#         folium.Rectangle(
#             bounds=bounds,
#             color=get_color(row["risk_category"]),
#             fill=True,
#             fill_opacity=0.4,
#             popup=f"""
#             Grid: {row['grid_id']}<br>
#             CRII: {round(row['crii'],2)}<br>
#             Risk: {row['risk_category']}
#             """
#         ).add_to(m)

#     except:
#         continue

# # Save map
# m.save("india_crii_map.html")

# print("India CRII map generated ✅")



import pandas as pd
import folium

# Load data
df = pd.read_csv("data/india_crii_results.csv")

# Create map
m = folium.Map(location=[22.5, 80], zoom_start=5)

# Color function
def get_color(risk):
    if risk == "Low":
        return "green"
    elif risk == "Moderate":
        return "orange"
    elif risk == "High":
        return "red"
    else:
        return "darkred"

# Add grid rectangles
for _, row in df.iterrows():
    try:
        bounds = [
            [row["lat_min"], row["lon_min"]],
            [row["lat_max"], row["lon_max"]]
        ]

        folium.Rectangle(
            bounds=bounds,
            color=get_color(row["risk_category"]),
            fill=True,
            fill_opacity=0.3,
            popup=f"""
            Grid: {row['grid_id']}<br>
            CRII: {round(row['crii'],2)}<br>
            Risk: {row['risk_category']}
            """
        ).add_to(m)

    except:
        continue

# -----------------------------
# ADD LEGEND (VERY IMPORTANT)
# -----------------------------
legend_html = '''
<div style="position: fixed; 
bottom: 50px; left: 50px; width: 150px; height: 120px; 
background-color: white; z-index:9999; font-size:14px;
border:2px solid grey; padding: 10px;">
<b>Risk Levels</b><br>
🟢 Low<br>
🟡 Moderate<br>
🔴 High<br>
⚫ Critical
</div>
'''

m.get_root().html.add_child(folium.Element(legend_html))

# Save map
m.save("india_crii_map.html")

print("India CRII map generated ✅")