# import streamlit as st
# import pandas as pd
# from geopy.geocoders import Nominatim
# import requests
# from rapidfuzz import fuzz

# # -----------------------------
# # CONFIG
# # -----------------------------
# st.set_page_config(page_title="CRII System", layout="centered")

# st.title("🌍 Climate Risk Intelligence System (CRII)")
# st.write("Enter any location in India to get climate risk analysis")

# # -----------------------------
# # LOAD DATA (CACHED)
# # -----------------------------
# @st.cache_data
# def load_data():
#     grid = pd.read_csv("data/india_grid.csv")
#     crii = pd.read_csv("data/india_crii_results.csv")
#     return grid, crii

# grid_df, crii_df = load_data()

# # -----------------------------
# # GEOCODER
# # -----------------------------
# geolocator = Nominatim(user_agent="crii_app")
# def smart_geocode(place):
#     try:
#         # STEP 1 — Try normal geocoding
#         location = geolocator.geocode(place + ", India", timeout=10)

#         if location:
#             return location.latitude, location.longitude

#     except:
#         pass

#     # STEP 2 — Try without India bias
#     try:
#         location = geolocator.geocode(place, timeout=10)

#         if location:
#             return location.latitude, location.longitude

#     except:
#         pass

#     # STEP 3 — SMART FALLBACK (YOUR DATA 🔥)
#     # Instead of hardcoding, use grid centers

#     best_match = None
#     best_score = 0

#     for _, row in grid_df.iterrows():
#         # Create pseudo location name using coordinates
#         grid_name = f"{row['lat_min']}_{row['lon_min']}"

#         score = fuzz.partial_ratio(place.lower(), grid_name.lower())

#         if score > best_score:
#             best_score = score
#             best_match = row

#     # If something matches weakly, return center of grid
#     if best_match is not None and best_score > 40:
#         lat = (best_match["lat_min"] + best_match["lat_max"]) / 2
#         lon = (best_match["lon_min"] + best_match["lon_max"]) / 2
#         return lat, lon

#     return None, None
# # -----------------------------
# # WEATHER API
# # -----------------------------
# API_KEY = "029a4bf0e7246078162240bee9931c35"

# def get_weather(lat, lon):
#     url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
#     try:
#         response = requests.get(url)
#         data = response.json()

#         if response.status_code != 200:
#             return None

#         return {
#             "description": data["weather"][0]["description"],
#             "temp": data["main"]["temp"],
#             "humidity": data["main"]["humidity"],
#             "wind": data["wind"]["speed"]
#         }
#     except:
#         return None

# # -----------------------------
# # GRID FINDER
# # -----------------------------
# def find_grid(lat, lon):
#     for _, row in grid_df.iterrows():
#         if (row["lat_min"] <= lat <= row["lat_max"] and
#             row["lon_min"] <= lon <= row["lon_max"]):
#             return int(row["grid_id"])
#     return None

# # -----------------------------
# # THREAT ANALYSIS
# # -----------------------------
# def get_threats(row):
#     threats = []

#     if row["lst_norm"] > 0.6:
#         threats.append("🔥 Heat Stress")

#     if row["flood_norm"] > 0.6:
#         threats.append("🌊 Flood Risk")

#     if row["veg_norm"] > 0.6:
#         threats.append("🌱 Vegetation Loss")

#     if row["urban_norm"] > 0.6:
#         threats.append("🏙 Urban Stress")

#     if not threats:
#         threats.append("No major threats")

#     return threats

# # -----------------------------
# # USER INPUT
# # -----------------------------
# place = st.text_input("📍 Enter Location")

# # -----------------------------
# # MAIN LOGIC
# # -----------------------------
# if place:
#     with st.spinner("Analyzing location..."):

#         try:
#             location = geolocator.geocode(place + ", India", timeout=10)
#         except:
#             location = None

#         if location is None:
#             st.error("❌ Location not found")
#         else:
#             lat, lon = location.latitude, location.longitude

#             grid_id = find_grid(lat, lon)

#             if grid_id is None:
#                 st.warning("⚠️ Location outside study area")
#             else:
#                 result = crii_df[crii_df["grid_id"] == grid_id]

#                 if result.empty:
#                     st.warning("⚠️ No data available")
#                 else:
#                     row = result.iloc[0]

#                     # -----------------------------
#                     # LOCATION INFO
#                     # -----------------------------
#                     st.success(f"📍 Location: {place.title()}")
#                     st.caption(f"📌 Coordinates: {round(lat,4)}, {round(lon,4)}")
#                     st.caption(f"🧭 Grid ID: {grid_id}")

#                     # -----------------------------
#                     # CRII OUTPUT
#                     # -----------------------------
#                     st.subheader("📊 Climate Risk Analysis")

#                     st.metric("🌍 CRII Score", round(row["crii"], 2))
#                     st.metric("⚠️ Risk Level", row["risk_category"])

#                     # Risk Color Indicator
#                     risk = row["risk_category"]

#                     if risk == "Low":
#                         st.success("🟢 Low Risk")
#                     elif risk == "Moderate":
#                         st.warning("🟡 Moderate Risk")
#                     elif risk == "High":
#                         st.error("🔴 High Risk")
#                     else:
#                         st.error("🚨 Critical Risk")

#                     # -----------------------------
#                     # THREATS
#                     # -----------------------------
#                     st.subheader("🚨 Main Threats")
#                     threats = get_threats(row)

#                     for t in threats:
#                         st.write(f"- {t}")

#                     # -----------------------------
#                     # WEATHER
#                     # -----------------------------
#                     weather = get_weather(lat, lon)

#                     st.subheader("🌦 Current Weather")

#                     if weather:
#                         st.write(f"Condition: {weather['description'].title()}")
#                         st.write(f"🌡 Temperature: {weather['temp']} °C")
#                         st.write(f"💧 Humidity: {weather['humidity']} %")
#                         st.write(f"🌬 Wind Speed: {weather['wind']} m/s")
#                     else:
#                         st.write("Weather data not available")











# import streamlit as st
# import pandas as pd
# from geopy.geocoders import Nominatim
# import requests
# from rapidfuzz import fuzz

# # -----------------------------
# # CONFIG
# # -----------------------------
# st.set_page_config(page_title="CRII System", layout="centered")

# st.title("🌍 Climate Risk Intelligence System (CRII)")
# st.write("Enter any location in India to get climate risk analysis")

# # -----------------------------
# # LOAD DATA (CACHED)
# # -----------------------------
# @st.cache_data
# def load_data():
#     grid = pd.read_csv("data/india_grid.csv")
#     crii = pd.read_csv("data/india_crii_results.csv")
#     return grid, crii

# grid_df, crii_df = load_data()

# # -----------------------------
# # GEOCODER
# # -----------------------------
# geolocator = Nominatim(user_agent="crii_app")

# # -----------------------------
# # SMART GEOCODER (NO HARDCODING)
# # -----------------------------
# def smart_geocode(place):
#     # STEP 1 — Try India-specific search
#     try:
#         location = geolocator.geocode(place + ", India", timeout=10)
#         if location:
#             return location.latitude, location.longitude
#     except:
#         pass

#     # STEP 2 — Try global search
#     try:
#         location = geolocator.geocode(place, timeout=10)
#         if location:
#             return location.latitude, location.longitude
#     except:
#         pass

#     # STEP 3 — Fallback using grid (DATA-DRIVEN, NOT HARDCODED)
#     best_match = None
#     best_score = 0

#     for _, row in grid_df.iterrows():
#         grid_repr = f"{row['lat_min']},{row['lon_min']}"

#         score = fuzz.partial_ratio(place.lower(), grid_repr.lower())

#         if score > best_score:
#             best_score = score
#             best_match = row

#     if best_match is not None and best_score > 40:
#         lat = (best_match["lat_min"] + best_match["lat_max"]) / 2
#         lon = (best_match["lon_min"] + best_match["lon_max"]) / 2
#         return lat, lon

#     return None, None

# # -----------------------------
# # WEATHER API
# # -----------------------------
# API_KEY = "029a4bf0e7246078162240bee9931c35"

# def get_weather(lat, lon):
#     url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
#     try:
#         response = requests.get(url)
#         data = response.json()

#         if response.status_code != 200:
#             return None

#         return {
#             "description": data["weather"][0]["description"],
#             "temp": data["main"]["temp"],
#             "humidity": data["main"]["humidity"],
#             "wind": data["wind"]["speed"]
#         }
#     except:
#         return None

# # -----------------------------
# # GRID FINDER
# # -----------------------------
# def find_grid(lat, lon):
#     for _, row in grid_df.iterrows():
#         if (row["lat_min"] <= lat <= row["lat_max"] and
#             row["lon_min"] <= lon <= row["lon_max"]):
#             return int(row["grid_id"])
#     return None

# # -----------------------------
# # THREAT ANALYSIS
# # -----------------------------
# def get_threats(row):
#     threats = []

#     if row["lst_norm"] > 0.6:
#         threats.append("🔥 Heat Stress")

#     if row["flood_norm"] > 0.6:
#         threats.append("🌊 Flood Risk")

#     if row["veg_norm"] > 0.6:
#         threats.append("🌱 Vegetation Loss")

#     if row["urban_norm"] > 0.6:
#         threats.append("🏙 Urban Stress")

#     if not threats:
#         threats.append("No major threats")

#     return threats

# # -----------------------------
# # USER INPUT
# # -----------------------------
# place = st.text_input("📍 Enter Location")

# # -----------------------------
# # MAIN LOGIC
# # -----------------------------
# if place:
#     with st.spinner("Analyzing location..."):

#         lat, lon = smart_geocode(place)

#         if lat is None:
#             st.error("❌ Location not found")
#         else:
#             grid_id = find_grid(lat, lon)

#             if grid_id is None:
#                 st.warning("⚠️ Location outside study area")
#             else:
#                 result = crii_df[crii_df["grid_id"] == grid_id]

#                 if result.empty:
#                     st.warning("⚠️ No data available")
#                 else:
#                     row = result.iloc[0]

#                     # -----------------------------
#                     # LOCATION INFO
#                     # -----------------------------
#                     st.success(f"📍 Location: {place.title()}")
#                     st.caption(f"📌 Coordinates: {round(lat,4)}, {round(lon,4)}")
#                     st.caption(f"🧭 Grid ID: {grid_id}")

#                     # -----------------------------
#                     # CRII OUTPUT
#                     # -----------------------------
#                     st.subheader("📊 Climate Risk Analysis")

#                     st.metric("🌍 CRII Score", round(row["crii"], 2))
#                     st.metric("⚠️ Risk Level", row["risk_category"])

#                     risk = row["risk_category"]

#                     if risk == "Low":
#                         st.success("🟢 Low Risk")
#                     elif risk == "Moderate":
#                         st.warning("🟡 Moderate Risk")
#                     elif risk == "High":
#                         st.error("🔴 High Risk")
#                     else:
#                         st.error("🚨 Critical Risk")

#                     # -----------------------------
#                     # THREATS
#                     # -----------------------------
#                     st.subheader("🚨 Main Threats")
#                     threats = get_threats(row)

#                     for t in threats:
#                         st.write(f"- {t}")

#                     # -----------------------------
#                     # WEATHER
#                     # -----------------------------
#                     weather = get_weather(lat, lon)

#                     st.subheader("🌦 Current Weather")

#                     if weather:
#                         st.write(f"Condition: {weather['description'].title()}")
#                         st.write(f"🌡 Temperature: {weather['temp']} °C")
#                         st.write(f"💧 Humidity: {weather['humidity']} %")
#                         st.write(f"🌬 Wind Speed: {weather['wind']} m/s")
#                     else:
#                         st.write("Weather data not available")


#Major Project/app.py
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import requests
from rapidfuzz import fuzz
import datetime

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="CRII System", layout="centered")

st.title("🌍 Climate Risk Intelligence System (CRII)")
st.write("Enter any location in India to get climate risk analysis")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    grid = pd.read_csv("data/india_grid.csv")
    crii = pd.read_csv("data/india_crii_results.csv")
    return grid, crii

grid_df, crii_df = load_data()

# -----------------------------
# GEOCODER
# -----------------------------
geolocator = Nominatim(user_agent="crii_app")

def smart_geocode(place):
    try:
        location = geolocator.geocode(place + ", India", timeout=10)
        if location:
            return location.latitude, location.longitude
    except:
        pass

    try:
        location = geolocator.geocode(place, timeout=10)
        if location:
            return location.latitude, location.longitude
    except:
        pass

    best_match = None
    best_score = 0

    for _, row in grid_df.iterrows():
        grid_repr = f"{row['lat_min']},{row['lon_min']}"
        score = fuzz.partial_ratio(place.lower(), grid_repr.lower())

        if score > best_score:
            best_score = score
            best_match = row

    if best_match is not None and best_score > 40:
        lat = (best_match["lat_min"] + best_match["lat_max"]) / 2
        lon = (best_match["lon_min"] + best_match["lon_max"]) / 2
        return lat, lon

    return None, None

# -----------------------------
# WEATHER + AQI
# -----------------------------
API_KEY = "029a4bf0e7246078162240bee9931c35"

def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        res = requests.get(url).json()

        if "main" not in res:
            return None

        sunrise = datetime.datetime.fromtimestamp(res["sys"]["sunrise"]).strftime('%H:%M')
        sunset = datetime.datetime.fromtimestamp(res["sys"]["sunset"]).strftime('%H:%M')

        return {
            "temp": res["main"]["temp"],
            "humidity": res["main"]["humidity"],
            "wind": res["wind"]["speed"],
            "desc": res["weather"][0]["description"],
            "sunrise": sunrise,
            "sunset": sunset
        }
    except:
        return None

def get_aqi(lat, lon):
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        res = requests.get(url).json()
        return res["list"][0]["main"]["aqi"]
    except:
        return None

# -----------------------------
# GRID FINDER
# -----------------------------
def find_grid(lat, lon):
    for _, row in grid_df.iterrows():
        if (row["lat_min"] <= lat <= row["lat_max"] and
            row["lon_min"] <= lon <= row["lon_max"]):
            return int(row["grid_id"])
    return None

# -----------------------------
# SMART THREAT ANALYSIS 🔥
# -----------------------------
def get_threats(row, weather):
    threats = []

    if row["lst_norm"] > 0.6:
        msg = "🔥 Heat Stress: High land surface temperature detected"
        if weather and weather["temp"] > 35:
            msg += " (Real-time heatwave conditions)"
        threats.append(msg)

    if row["flood_norm"] > 0.6:
        threats.append("🌊 Flood Risk: High water accumulation probability")

    if row["veg_norm"] > 0.6:
        threats.append("🌱 Vegetation Loss: Poor vegetation health detected")

    if row["urban_norm"] > 0.6:
        threats.append("🏙 Urban Stress: High built-up density impact")

    if not threats:
        threats.append("✅ No major climate threats detected")

    return threats

# -----------------------------
# WEATHER INSIGHTS
# -----------------------------
def weather_insights(weather):
    insights = []

    if weather["temp"] > 35:
        insights.append("🔥 Extreme heat — avoid outdoor exposure")

    if weather["humidity"] > 80:
        insights.append("💧 High humidity — discomfort likely")

    if weather["wind"] > 10:
        insights.append("🌬 Strong winds detected")

    return insights

# -----------------------------
# USER INPUT
# -----------------------------
place = st.text_input("📍 Enter Location")

# -----------------------------
# MAIN LOGIC
# -----------------------------
if place:
    with st.spinner("Analyzing location..."):

        lat, lon = smart_geocode(place)

        if lat is None:
            st.error("❌ Location not found")
        else:
            grid_id = find_grid(lat, lon)

            if grid_id is None:
                st.warning("⚠️ Location outside study area")
            else:
                row = crii_df[crii_df["grid_id"] == grid_id].iloc[0]

                weather = get_weather(lat, lon)
                aqi = get_aqi(lat, lon)

                # -----------------------------
                # LOCATION
                # -----------------------------
                st.success(f"📍 {place.title()}")
                st.caption(f"{round(lat,4)}, {round(lon,4)}")

                # -----------------------------
                # CRII
                # -----------------------------
                st.subheader("📊 Climate Risk")

                st.metric("CRII Score", round(row["crii"], 2))
                st.metric("Risk Level", row["risk_category"])

                # -----------------------------
                # THREATS
                # -----------------------------
                st.subheader("🚨 Threat Analysis")
                threats = get_threats(row, weather)

                for t in threats:
                    st.write("-", t)

                # -----------------------------
                # WEATHER
                # -----------------------------
                if weather:
                    st.subheader("🌦 Weather Details")
                    st.write(f"🌡 Temp: {weather['temp']} °C")
                    st.write(f"💧 Humidity: {weather['humidity']} %")
                    st.write(f"🌬 Wind: {weather['wind']} m/s")
                    st.write(f"🌅 Sunrise: {weather['sunrise']}")
                    st.write(f"🌇 Sunset: {weather['sunset']}")

                    st.subheader("🧠 Weather Insights")
                    for i in weather_insights(weather):
                        st.write("-", i)

                # -----------------------------
                # AQI
                # -----------------------------
                if aqi:
                    st.subheader("🌫 Air Quality Index")
                    st.write(f"AQI Level: {aqi}")