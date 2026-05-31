# Major Project/app.py
# CRII — Climate Risk Intelligence System
# Fully upgraded: clean UX, no internal API details exposed to user,
# richer agentic output, descriptive threat cards.

import os
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import requests
import datetime

try:
    from crii_agent import run_crii_agent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

# ── PAGE CONFIG ──────────────────────────────────────────────────
st.set_page_config(
    page_title="CRII — Climate Risk Intelligence",
    page_icon="🌍",
    layout="wide"
)

# ── CUSTOM CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    
    /* Main app background */
    .stApp {
        background-color: #0E1117;
        color: white;
    }
            
    /* Tighten top padding */
    .block-container { padding-top: 1.5rem; }

    /* Risk badge pill */
    .risk-pill {
        display: inline-block;
        padding: 4px 16px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        margin-top: 4px;
    }
    .risk-Low      { background:#d4edda; color:#155724; }
    .risk-Moderate { background:#fff3cd; color:#856404; }
    .risk-High     { background:#ffe0b2; color:#e65100; }
    .risk-Critical { background:#f8d7da; color:#721c24; }

    /* Agent output box */
    .agent-box {
        background: #f8f9fa;
        border-left: 3px solid #1a73e8;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        font-size: 15px;
        line-height: 1.8;
    }

    /* Metric card tweak */
    [data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px 14px;
    }

    /* Sidebar — dark look */
    section[data-testid="stSidebar"] {
        background-color: #0E1117 !important;
    }

    /* Sidebar text */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
            
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR — user-facing info only, no API internals ────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/ISRO_logo.svg/200px-ISRO_logo.svg.png",
             width=60)
    st.markdown("## 🌍 CRII")
    st.markdown("**Climate Risk Intelligence System**")
    st.markdown("_Satellite-powered risk analysis for India_")
    st.divider()

    st.markdown("#### 📡 Data Sources")
    st.markdown("""
- 🌊 **Flood** — JRC Global Surface Water
- 🌡 **Heat** — MODIS Land Surface Temp
- 🌱 **Vegetation** — MODIS NDVI
- 🏙 **Urban** — GHSL Built Surface
- 🌧 **Rainfall** — ERA5 Reanalysis
    """)
    st.divider()

    st.markdown("#### ℹ️ How it works")
    st.markdown("""
1. Enter any Indian city or region
2. We locate it on our 0.5° satellite grid
3. AI analyses 5 risk dimensions
4. Live weather is overlaid on the score
    """)
    st.divider()

    st.caption("Satellite data: 2023 annual composites")
    st.caption("Weather: OpenWeatherMap live API")
    st.caption("Grid: 3,840 cells covering India")

# ── HEADER ───────────────────────────────────────────────────────
st.markdown("# 🌍 Climate Risk Intelligence System")
st.markdown("##### AI-powered satellite risk analysis for any location in India")
st.divider()

# ── DATA LOADING ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    grid = pd.read_csv("data/india_grid.csv")
    crii = pd.read_csv("data/india_crii_results.csv")
    return grid, crii

@st.cache_data
def load_districts():
    try:
        return pd.read_csv("data/districts_india.csv")
    except FileNotFoundError:
        return None

grid_df, crii_df = load_data()
districts_df = load_districts()

# ── GEOCODING ────────────────────────────────────────────────────
geolocator = Nominatim(user_agent="crii_app_v2")

def smart_geocode(place):
    try:
        loc = geolocator.geocode(place + ", India", timeout=10)
        if loc: return loc.latitude, loc.longitude
    except: pass
    try:
        loc = geolocator.geocode(place, timeout=10)
        if loc: return loc.latitude, loc.longitude
    except: pass
    if districts_df is not None:
        p = place.lower().strip()
        m = districts_df[
            districts_df["district"].str.lower().str.contains(p, na=False) |
            districts_df["state"].str.lower().str.contains(p, na=False)
        ]
        if len(m) > 0:
            return float(m.iloc[0]["lat"]), float(m.iloc[0]["lon"])
    return None, None

# ── WEATHER ──────────────────────────────────────────────────────
OWM_KEY = "029a4bf0e7246078162240bee9931c35"

def get_weather(lat, lon):
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric",
            timeout=8
        ).json()
        if "main" not in r: return None
        return {
            "temp":     r["main"]["temp"],
            "feels":    r["main"]["feels_like"],
            "humidity": r["main"]["humidity"],
            "wind":     r["wind"]["speed"],
            "desc":     r["weather"][0]["description"],
            "icon":     r["weather"][0]["main"],
            "sunrise":  datetime.datetime.fromtimestamp(r["sys"]["sunrise"]).strftime('%H:%M'),
            "sunset":   datetime.datetime.fromtimestamp(r["sys"]["sunset"]).strftime('%H:%M'),
        }
    except: return None

def get_aqi(lat, lon):
    try:
        r = requests.get(
            f"http://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={OWM_KEY}",
            timeout=8
        ).json()
        return r["list"][0]["main"]["aqi"]
    except: return None

AQI_LABELS  = {1:"Good 😊", 2:"Fair 🙂", 3:"Moderate 😐", 4:"Poor 😷", 5:"Very Poor ☠️"}
AQI_COLORS  = {1:"#d4edda", 2:"#d4edda", 3:"#fff3cd", 4:"#ffe0b2", 5:"#f8d7da"}
ICON_MAP    = {
    "Clear":"☀️","Clouds":"⛅","Rain":"🌧","Drizzle":"🌦",
    "Thunderstorm":"⛈","Snow":"❄️","Mist":"🌫","Fog":"🌫","Haze":"🌫"
}

# ── GRID FINDER ──────────────────────────────────────────────────
def find_grid(lat, lon):
    m = grid_df[
        (grid_df["lat_min"] <= lat) & (lat <= grid_df["lat_max"]) &
        (grid_df["lon_min"] <= lon) & (lon <= grid_df["lon_max"])
    ]
    return int(m.iloc[0]["grid_id"]) if len(m) > 0 else None

# ── RISK COLOUR HELPERS ──────────────────────────────────────────
RISK_COLORS = {
    "Low":      ("#155724","#d4edda"),
    "Moderate": ("#856404","#fff3cd"),
    "High":     ("#e65100","#ffe0b2"),
    "Critical": ("#721c24","#f8d7da"),
}
RISK_ICONS = {"Low":"🟢","Moderate":"🟡","High":"🟠","Critical":"🔴"}

def risk_bar_color(val):
    if val < 0.25: return "#28a745"
    if val < 0.50: return "#ffc107"
    if val < 0.75: return "#fd7e14"
    return "#dc3545"

# ── RULE-BASED FALLBACK (when no AI key) ─────────────────────────
COMPONENT_DESCRIPTIONS = {
    "flood_norm": {
        "name": "🌊 Flood & Surface Water",
        "low":      "Minimal surface water presence. Low flood exposure for this zone.",
        "moderate": "Moderate persistent surface water detected via JRC satellite data. Seasonal flooding possible.",
        "high":     "High surface water persistence. Significant flood risk — riverine or coastal inundation likely.",
    },
    "lst_norm": {
        "name": "🌡 Land Surface Temperature",
        "low":      "Temperature within normal range for this agro-climatic zone.",
        "moderate": "Above-average land surface temperature detected. Heat stress risk for outdoor workers and agriculture.",
        "high":     "Critically elevated land surface temperature. Urban heat island or drought conditions likely.",
    },
    "veg_norm": {
        "name": "🌱 Vegetation Health",
        "low":      "Vegetation is healthy and above the zone baseline. Ecosystem stable.",
        "moderate": "Vegetation stress detected — NDVI below zone baseline. Possible drought, deforestation, or seasonal die-off.",
        "high":     "Severe vegetation stress. Significant ecosystem degradation. Risk of soil erosion and reduced carbon sequestration.",
    },
    "urban_norm": {
        "name": "🏙 Urban Density & Stress",
        "low":      "Low built-up surface density. Minimal urban heat island effect.",
        "moderate": "Moderate urban density. Some heat island amplification and increased surface runoff.",
        "high":     "High urban concentration. Strong heat island effect, reduced green space, and stormwater risk.",
    },
    "rainfall_norm": {
        "name": "🌧 Rainfall Pattern",
        "low":      "Rainfall within or below zone norms. No excess precipitation stress.",
        "moderate": "Above-average rainfall for this zone. Waterlogging and soil saturation risk.",
        "high":     "Exceptionally high rainfall relative to zone baseline. Flood compound risk is elevated.",
    },
}

def get_level(val):
    if val < 0.25: return "low"
    if val < 0.50: return "moderate"
    return "high"

def rule_based_analysis(row, weather):
    """Generate descriptive threat cards without AI."""
    cards = []
    for key, info in COMPONENT_DESCRIPTIONS.items():
        val   = float(row[key])
        level = get_level(val)
        if level == "low":
            continue
        desc = info[level]
        # Weather cross-reference
        if key == "lst_norm" and weather and weather["temp"] > 35:
            desc += f" Current live temperature of {weather['temp']}°C confirms active heatwave conditions."
        if key == "flood_norm" and weather and "rain" in weather["desc"].lower():
            desc += " Active rainfall detected right now — risk is elevated in real time."
        cards.append({
            "name":  info["name"],
            "level": level.capitalize(),
            "val":   val,
            "desc":  desc,
        })

    if not cards:
        cards.append({
            "name":  "✅ Overall Environment",
            "level": "Low",
            "val":   0.0,
            "desc":  "No significant environmental stress detected across any risk dimension. This location currently presents low climate risk relative to its agro-climatic zone baseline.",
        })
    return cards

# ── SEARCH BAR ───────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    place = st.text_input(
        "📍 Location",
        placeholder="e.g. Chennai, Assam, Leh, Wayanad...",
        label_visibility="collapsed"
    )
with col_btn:
    search = st.button("Analyse 🔍", use_container_width=True, type="primary")

# Example quick links
st.caption("Try: &nbsp;&nbsp; **Mumbai** &nbsp;·&nbsp; **Assam** &nbsp;·&nbsp; **Leh** &nbsp;·&nbsp; **Wayanad** &nbsp;·&nbsp; **Jaisalmer** &nbsp;·&nbsp; **Chennai**")

# ── MAIN ANALYSIS ────────────────────────────────────────────────
if place:
    with st.spinner(f"Locating {place.title()}..."):
        lat, lon = smart_geocode(place)

    if lat is None:
        st.error("❌ Location not found. Please try a city, district, or region name within India.")
        st.stop()

    grid_id = find_grid(lat, lon)
    if grid_id is None:
        st.warning("⚠️ This location falls outside the India study area (lat 6°–38°N, lon 68°–98°E).")
        st.stop()

    row     = crii_df[crii_df["grid_id"] == grid_id].iloc[0]
    weather = get_weather(lat, lon)
    aqi     = get_aqi(lat, lon)

    zone     = str(row.get("agro_zone", "")).replace("_", " ")
    crii_val = round(float(row["crii"]), 3)
    uncert   = round(float(row.get("crii_uncertainty", 0.05)), 3)
    category = str(row["risk_category"])
    fg, bg   = RISK_COLORS.get(category, ("#333","#eee"))

    # ── LOCATION HEADER ──────────────────────────────────────────
    st.markdown(f"## 📍 {place.title()}")

    meta_parts = [f"{round(lat,4)}°N, {round(lon,4)}°E"]
    if zone:
        meta_parts.append(f"Agro-climatic zone: **{zone}**")
    st.markdown("  ·  ".join(meta_parts))
    st.divider()

    # ── THREE-SECTION LAYOUT ─────────────────────────────────────
    col_score, col_weather, col_aqi = st.columns([2, 2, 1], gap="medium")

    # CRII SCORE CARD
    with col_score:
        st.markdown("#### 🎯 Climate Risk Score")
        st.markdown(
            f"""
            <div style="background:{bg};border-radius:12px;padding:16px 20px;margin-bottom:8px;">
                <div style="font-size:38px;font-weight:700;color:{fg};">{crii_val}</div>
                <div style="font-size:13px;color:{fg};opacity:0.75;">± {uncert} uncertainty</div>
                <div style="margin-top:8px;">
                    <span class="risk-pill risk-{category}">{RISK_ICONS[category]} {category} Risk</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.caption(f"Score range: 0 (safe) → 1 (critical)  ·  Based on 2023 satellite composites")

    # WEATHER CARD
    with col_weather:
        st.markdown("#### 🌦 Live Weather")
        if weather:
            icon = ICON_MAP.get(weather["icon"], "🌤")
            st.markdown(
                f"""
                <div style="background:#f8f9fa;border-radius:12px;padding:16px 20px;">
                    <div style="font-size:32px;font-weight:600;">{icon} {weather['temp']}°C</div>
                    <div style="font-size:13px;color:#555;margin-top:4px;">Feels like {weather['feels']}°C &nbsp;·&nbsp; {weather['desc'].title()}</div>
                    <div style="margin-top:10px;font-size:13px;color:#444;">
                        💧 {weather['humidity']}% humidity &nbsp;·&nbsp; 🌬 {weather['wind']} m/s wind<br>
                        🌅 {weather['sunrise']} sunrise &nbsp;·&nbsp; 🌇 {weather['sunset']} sunset
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("Weather data unavailable")

    # AQI CARD
    with col_aqi:
        st.markdown("#### 🌫 Air Quality")
        if aqi:
            aqi_label = AQI_LABELS.get(aqi, "Unknown")
            aqi_color = AQI_COLORS.get(aqi, "#eee")
            st.markdown(
                f"""
                <div style="background:{aqi_color};border-radius:12px;padding:16px 20px;text-align:center;">
                    <div style="font-size:32px;font-weight:700;">{aqi}</div>
                    <div style="font-size:14px;font-weight:500;margin-top:4px;">{aqi_label}</div>
                    <div style="font-size:11px;color:#555;margin-top:6px;">AQI Index (1–5)</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("AQI unavailable")

    st.divider()

    # ── RISK COMPONENTS BAR CHART ─────────────────────────────────
    st.markdown("#### 📊 Risk Component Breakdown")
    components = [
        ("🌊 Flood",          float(row["flood_norm"])),
        ("🌡 Heat",           float(row["lst_norm"])),
        ("🌱 Vegetation",     float(row["veg_norm"])),
        ("🏙 Urban",          float(row["urban_norm"])),
        ("🌧 Rainfall",       float(row["rainfall_norm"])),
    ]

    for name, val in components:
        bar_pct = int(val * 100)
        color   = risk_bar_color(val)
        level   = ["Low","Moderate","High","Critical"][
            0 if val < 0.25 else 1 if val < 0.50 else 2 if val < 0.75 else 3
        ]
        st.markdown(
            f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px;">
                    <span>{name}</span>
                    <span style="color:{color};font-weight:600;">{round(val,2)} — {level}</span>
                </div>
                <div style="background:#e9ecef;border-radius:6px;height:10px;overflow:hidden;">
                    <div style="width:{bar_pct}%;background:{color};height:100%;border-radius:6px;
                                transition:width 0.8s ease;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # ── AI INTELLIGENT ANALYSIS ──────────────────────────────────
    st.markdown("#### 🧠 Intelligent Risk Analysis")

    use_agent = AGENT_AVAILABLE and (
        bool(os.environ.get("ANTHROPIC_API_KEY")) or
        bool(os.environ.get("GEMINI_API_KEY"))
    )

    if use_agent:
        # Show a nice step-by-step status while agent runs
        status_box = st.empty()
        status_box.markdown(
            """
            <div style="background:#e8f4fd;border-radius:8px;padding:12px 16px;font-size:13px;color:#1a73e8;">
                🤖 <strong>AI Agent is working...</strong><br>
                Fetching satellite risk data → Loading climate zone context → Retrieving live weather → Synthesizing analysis
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.spinner(""):
            agent_response = run_crii_agent(place, lat, lon)

        status_box.empty()

        # Display agent response in a styled box
        st.markdown(
            f"""
            <div class="agent-box">
                {agent_response.replace(chr(10), '<br>')}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.caption("🤖 Analysis generated by AI — cross-referencing satellite data, zone climate knowledge, and live weather.")

    else:
        # Rich rule-based fallback cards
        st.markdown(
            """
            <div style="background:#f8f9fa;border-radius:8px;padding:10px 14px;
                        font-size:13px;color:#555;margin-bottom:12px;">
                📊 Showing satellite-based analysis. All risk signals are derived from 2023 satellite composites
                cross-referenced with India's agro-climatic zone baselines.
            </div>
            """,
            unsafe_allow_html=True
        )

        cards = rule_based_analysis(row, weather)

        for card in cards:
            fg2, bg2 = RISK_COLORS.get(card["level"], ("#333","#f8f9fa"))
            st.markdown(
                f"""
                <div style="background:{bg2};border-radius:10px;padding:14px 18px;
                            margin-bottom:10px;border-left:4px solid {fg2};">
                    <div style="font-size:15px;font-weight:600;color:{fg2};margin-bottom:6px;">
                        {card['name']} &nbsp;
                        <span style="font-size:12px;font-weight:400;
                                     background:{fg2};color:white;padding:2px 8px;
                                     border-radius:12px;">{card['level']}</span>
                    </div>
                    <div style="font-size:14px;color:#333;line-height:1.7;">{card['desc']}</div>
                    <div style="margin-top:8px;">
                        <div style="background:#dee2e6;border-radius:4px;height:6px;overflow:hidden;">
                            <div style="width:{int(card['val']*100)}%;background:{fg2};height:100%;border-radius:4px;"></div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Weather alerts section
        if weather:
            alerts = []
            if weather["temp"] < 5:
                alerts.append(("🥶","Near-Freezing Alert",
                    f"Current temperature of {weather['temp']}°C is near or below freezing. "
                    "Cold stress risk for outdoor workers, livestock, and agriculture. "
                    "Frost damage to crops is possible overnight."))
            if weather["temp"] > 40:
                alerts.append(("🔥","Extreme Heat Alert",
                    f"Temperature of {weather['temp']}°C constitutes a heatwave. "
                    "Avoid outdoor activity between 11am–4pm. Hydration critical. "
                    "High risk for elderly, outdoor workers, and livestock."))
            elif weather["temp"] > 35:
                alerts.append(("🌡","Heat Warning",
                    f"Temperature of {weather['temp']}°C is elevated. Combined with "
                    f"{weather['humidity']}% humidity, heat index is significantly higher than air temperature."))
            if weather["humidity"] > 85:
                alerts.append(("💧","High Humidity",
                    f"Humidity at {weather['humidity']}% significantly raises the perceived temperature "
                    "and reduces the body's ability to cool itself through perspiration."))
            if weather["wind"] > 15:
                alerts.append(("🌬","Strong Wind Advisory",
                    f"Wind speed of {weather['wind']} m/s. Risk of structural damage to temporary structures, "
                    "crop lodging, and power disruption."))
            if "rain" in weather["desc"].lower() or "storm" in weather["desc"].lower():
                alerts.append(("🌧","Active Precipitation",
                    f"Live condition: {weather['desc'].title()}. "
                    "If flood score is moderate or high, real-time risk may exceed the satellite baseline."))

            if alerts:
                st.markdown("#### ⚡ Live Weather Alerts")
                for icon, title, desc in alerts:
                    st.markdown(
                        f"""
                        <div style="background:#fff8e1;border-left:4px solid #f9a825;
                                    border-radius:8px;padding:12px 16px;margin-bottom:8px;">
                            <div style="font-size:14px;font-weight:600;margin-bottom:4px;">
                                {icon} {title}
                            </div>
                            <div style="font-size:13px;color:#444;line-height:1.6;">{desc}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
