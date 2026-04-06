import pandas as pd
from geopy.geocoders import Nominatim

# Load data
grid_df = pd.read_csv("data/india_grid.csv")
crii_df = pd.read_csv("data/india_crii_results.csv")

# Initialize geocoder
geolocator = Nominatim(user_agent="crii_app")

# Function to find grid
def find_grid(lat, lon):
    for _, row in grid_df.iterrows():
        if (row["lat_min"] <= lat <= row["lat_max"] and
            row["lon_min"] <= lon <= row["lon_max"]):
            return int(row["grid_id"])
    return None

import requests

# API_KEY = "2df9a2d9f5ff7cee688f587a32d7f606"
API_KEY = "029a4bf0e7246078162240bee9931c35"

def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
    response = requests.get(url)
    data = response.json()

    # DEBUG PRINT (add this)
    print("\nDEBUG Weather Response:", data)

    if response.status_code != 200:
        return None

    weather = {
        "description": data["weather"][0]["description"],
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "wind": data["wind"]["speed"]
    }

    return weather
    
def get_threats(row):
    threats = []

    if row["lst_norm"] > 0.6:
        threats.append("Heat Stress 🔥")

    if row["flood_norm"] > 0.6:
        threats.append("Flood Risk 🌊")

    if row["veg_norm"] > 0.6:
        threats.append("Vegetation Loss 🌱")

    if row["urban_norm"] > 0.6:
        threats.append("Urban Stress 🏙")

    if not threats:
        threats.append("No major threats")

    return threats
# Take user input
place = input("Enter location: ")

# Convert location → coordinates
location = geolocator.geocode(place + ", India")

if location is None:
    print("Location not found")
else:
    lat, lon = location.latitude, location.longitude

    grid_id = find_grid(lat, lon)

    if grid_id is None:
        print("Location outside study area")
    else:
        result = crii_df[crii_df["grid_id"] == grid_id]

        if result.empty:
            print("No data available")
        else:
            row = result.iloc[0]

            print("\n📍 Location:", place.title())
            print("📌 Coordinates:", round(lat, 4), ",", round(lon, 4))
            print("🧭 Grid ID:", grid_id)
            print("🌍 CRII Score:", round(row["crii"], 2))
            print("⚠️ Risk Level:", row["risk_category"])

            # Threat breakdown
            threats = get_threats(row)

            print("\n🚨 Main Threats:")
            for t in threats:
                print("-", t)
            
            weather = get_weather(lat, lon)

            if weather:
                print("\n🌦 Current Weather:")
                print("Condition:", weather["description"].title())
                print("🌡 Temperature:", weather["temp"], "°C")
                print("💧 Humidity:", weather["humidity"], "%")
                print("🌬 Wind Speed:", weather["wind"], "m/s")
            else:
                print("\nWeather data not available")