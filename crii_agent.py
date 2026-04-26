# # crii_agent/crii_agent.py
# #
# # FREE VERSION — powered by Google Gemini 2.0 Flash
# # Free tier: 1,500 requests/day, no credit card required
# #
# # Setup:
# #   pip install google-generativeai
# #   Get free key: https://aistudio.google.com/apikey
# #   Windows:   set GEMINI_API_KEY=your_key
# #   Mac/Linux: export GEMINI_API_KEY=your_key
# #
# # To switch back to Claude later (better quality):
# #   pip install anthropic
# #   Set ANTHROPIC_API_KEY instead, and change USE_GEMINI = False below

# import os
# import json
# import datetime
# import requests
# import pandas as pd
# from dotenv import load_dotenv

# load_dotenv()
# # -----------------------------
# # SWITCH: Set to False to use Claude instead
# # -----------------------------
# USE_GEMINI = True

# # -----------------------------
# # LOAD DATA ONCE (module-level cache)
# # -----------------------------
# _crii_df = None
# _grid_df = None

# def _load_data():
#     global _crii_df, _grid_df
#     if _crii_df is None:
#         _crii_df = pd.read_csv("data/india_crii_results.csv")
#         _grid_df = pd.read_csv("data/india_grid.csv")

# # ================================================================
# # TOOL FUNCTIONS
# # These are the same regardless of which LLM you use.
# # ================================================================

# def get_crii_data(lat: float, lon: float) -> dict:
#     """Retrieve satellite-derived CRII scores for a lat/lon location."""
#     _load_data()
#     match = _grid_df[
#         (_grid_df["lat_min"] <= lat) & (lat <= _grid_df["lat_max"]) &
#         (_grid_df["lon_min"] <= lon) & (lon <= _grid_df["lon_max"])
#     ]
#     if len(match) == 0:
#         return {"error": "Location outside India study area (lat 6–38, lon 68–98)"}

#     grid_id = int(match.iloc[0]["grid_id"])
#     rows = _crii_df[_crii_df["grid_id"] == grid_id]
#     if len(rows) == 0:
#         return {"error": f"No CRII data for grid_id {grid_id}"}

#     row = rows.iloc[0]
#     return {
#         "grid_id":          grid_id,
#         "crii_score":       round(float(row["crii"]), 3),
#         "uncertainty":      round(float(row.get("crii_uncertainty", 0.05)), 3),
#         "risk_category":    str(row["risk_category"]),
#         "agro_zone":        str(row.get("agro_zone", "Unknown")),
#         "data_completeness": round(float(row.get("data_completeness", 1.0)), 2),
#         "components": {
#             "flood_norm":    round(float(row["flood_norm"]), 3),
#             "lst_norm":      round(float(row["lst_norm"]), 3),
#             "veg_norm":      round(float(row["veg_norm"]), 3),
#             "urban_norm":    round(float(row["urban_norm"]), 3),
#             "rainfall_norm": round(float(row["rainfall_norm"]), 3),
#         }
#     }

# OWM_API_KEY = "029a4bf0e7246078162240bee9931c35"

# def get_live_weather(lat: float, lon: float) -> dict:
#     """Fetch real-time weather and AQI for a location."""
#     result = {}
#     try:
#         res = requests.get(
#             f"https://api.openweathermap.org/data/2.5/weather"
#             f"?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric",
#             timeout=8
#         ).json()
#         if "main" in res:
#             temp, humidity, wind = res["main"]["temp"], res["main"]["humidity"], res["wind"]["speed"]
#             desc = res["weather"][0]["description"]
#             hazards = []
#             if temp > 40:   hazards.append("extreme_heatwave")
#             elif temp > 35: hazards.append("heatwave")
#             if temp < 5:    hazards.append("near_freezing")
#             if humidity > 85: hazards.append("high_humidity")
#             if wind > 15:   hazards.append("strong_winds")
#             if "rain"  in desc.lower(): hazards.append("active_rainfall")
#             if "storm" in desc.lower() or "thunder" in desc.lower(): hazards.append("storm")
#             result["weather"] = {
#                 "temperature_c": temp, "humidity_pct": humidity,
#                 "wind_ms": wind, "condition": desc, "active_hazards": hazards,
#                 "sunrise": datetime.datetime.fromtimestamp(res["sys"]["sunrise"]).strftime('%H:%M'),
#                 "sunset":  datetime.datetime.fromtimestamp(res["sys"]["sunset"]).strftime('%H:%M'),
#             }
#     except Exception as e:
#         result["weather_error"] = str(e)

#     try:
#         res = requests.get(
#             f"http://api.openweathermap.org/data/2.5/air_pollution"
#             f"?lat={lat}&lon={lon}&appid={OWM_API_KEY}",
#             timeout=8
#         ).json()
#         aqi = res["list"][0]["main"]["aqi"]
#         result["aqi"] = {"value": aqi, "label": {1:"Good",2:"Fair",3:"Moderate",4:"Poor",5:"Very Poor"}.get(aqi)}
#     except Exception as e:
#         result["aqi_error"] = str(e)

#     return result

# def get_risk_context(agro_zone: str, month: int) -> dict:
#     """Return domain knowledge about an agro-climatic zone and current season."""
#     season = ("winter" if month in [12,1,2] else "pre_monsoon" if month in [3,4,5]
#               else "monsoon" if month in [6,7,8,9] else "post_monsoon")
#     profiles = {
#         "Western_Himalayas": {
#             "typical_hazards": ["glacial_lake_outburst","landslide","cold_stress","flash_flood"],
#             "monsoon_timing": "July–September (Western disturbances in winter)",
#             "note": "Surface water here is often glacial melt, not flood risk. Distinguish carefully.",
#             "high_risk_months": [7,8,9],
#         },
#         "Western_Ghats": {
#             "typical_hazards": ["landslide","extreme_rainfall","flood"],
#             "monsoon_timing": "June–September (Southwest Monsoon, heaviest in India)",
#             "note": "Receives 2000–6000mm annual rainfall. Flood and landslide risk very high Jun–Sep.",
#             "high_risk_months": [6,7,8,9],
#         },
#         "East_Coast": {
#             "typical_hazards": ["cyclone","storm_surge","flood","drought"],
#             "monsoon_timing": "October–December (Northeast Monsoon)",
#             "note": "Cyclone risk Oct–Dec from Bay of Bengal. Chennai and Andhra coast most exposed.",
#             "high_risk_months": [10,11,12],
#         },
#         "Trans_Gangetic_Plain": {
#             "typical_hazards": ["heat_stress","fog","flood","crop_drought"],
#             "monsoon_timing": "July–September",
#             "note": "Extreme summer heat (May–Jun). Dense winter fog disrupts transport.",
#             "high_risk_months": [5,6,7,8],
#         },
#         "Middle_Gangetic_Plain": {
#             "typical_hazards": ["flood","heat_stress","waterlogging"],
#             "monsoon_timing": "June–September",
#             "note": "Bihar and UP flood regularly due to Himalayan river overflow.",
#             "high_risk_months": [7,8,9],
#         },
#         "Eastern_Himalayas": {
#             "typical_hazards": ["landslide","flood","extreme_rainfall"],
#             "monsoon_timing": "May–October (among earliest monsoon onset in India)",
#             "note": "Cherrapunji region — world's highest rainfall. Flash floods common.",
#             "high_risk_months": [6,7,8,9],
#         },
#         "Western_Plateau": {
#             "typical_hazards": ["drought","heat_stress","water_scarcity"],
#             "monsoon_timing": "June–September (often deficient)",
#             "note": "Rajasthan — chronic drought zone. Low rainfall reliability.",
#             "high_risk_months": [4,5,6],
#         },
#         "Southern_Peninsula": {
#             "typical_hazards": ["drought","heat_stress","water_stress"],
#             "monsoon_timing": "June–September SW + Oct–Dec NE Monsoon",
#             "note": "Receives both monsoons but inter-annual variability is high.",
#             "high_risk_months": [4,5,10,11],
#         },
#         "West_Coast": {
#             "typical_hazards": ["extreme_rainfall","flood","landslide","coastal_erosion"],
#             "monsoon_timing": "June–September (Kerala onset ~June 1)",
#             "note": "Kerala coast — first monsoon landfall in India. Flooding and landslides severe.",
#             "high_risk_months": [6,7,8],
#         },
#     }
#     p = profiles.get(agro_zone, {
#         "typical_hazards": ["flood","heat_stress","drought"],
#         "monsoon_timing": "June–September",
#         "note": "Standard Indian monsoon zone.",
#         "high_risk_months": [7,8,9],
#     })
#     return {
#         "agro_zone": agro_zone,
#         "current_season": season,
#         "current_month": month,
#         "is_high_risk_season": month in p.get("high_risk_months",[]),
#         "typical_hazards": p["typical_hazards"],
#         "monsoon_timing": p["monsoon_timing"],
#         "domain_note": p["note"],
#     }

# # Tool dispatcher — same for both providers
# TOOL_MAP = {
#     "get_crii_data":    get_crii_data,
#     "get_live_weather": get_live_weather,
#     "get_risk_context": get_risk_context,
# }

# def dispatch_tool(name: str, args: dict) -> str:
#     fn = TOOL_MAP.get(name)
#     if fn is None:
#         return json.dumps({"error": f"Unknown tool: {name}"})
#     return json.dumps(fn(**args), indent=2)

# # ================================================================
# # SYSTEM PROMPT (shared)
# # ================================================================
# SYSTEM_PROMPT = """You are CRII-Agent, an expert climate risk analyst for India with deep knowledge
# of regional geography, monsoon patterns, and satellite-derived environmental data.

# ALWAYS call all three tools before writing your response:
#   1. get_crii_data      — satellite scores
#   2. get_risk_context   — zone + seasonal knowledge
#   3. get_live_weather   — current ground conditions

# Then write a rich, descriptive, location-specific risk report using this exact structure:

# ---

# 📍 **[Location Name] — Climate Context**
# Write 2–3 sentences describing this location's geography, climate zone, and what makes it
# climatically unique. Be specific — mention the actual region, landscape, or weather pattern.
# Do NOT write generic text.

# ---

# 🎯 **Risk Score: [X.XXX ± X.XXX] — [Category]**
# In 2–3 sentences, explain what this score means IN THIS SPECIFIC PLACE.
# Which components are the primary drivers? Is the score expected for this zone or surprising?
# Compare to what you'd expect for this climate zone.

# ---

# ⚠️ **Active Risk Signals**

# For each significant risk (score > 0.25), write a SHORT PARAGRAPH (3–4 sentences) explaining:
# - What the satellite data shows and why it matters HERE
# - Whether the signal is genuine or ambiguous for this location
#   (e.g. glacial meltwater channels in Leh register as surface water — not flood risk)
# - How it interacts with the current season and live weather

# Be honest about ambiguity — if a signal is likely an artifact or has a non-obvious explanation,
# say so explicitly.

# ---

# 🌦 **Current Ground Conditions**
# Describe the live weather in the context of the CRII score. Is today's weather amplifying
# the satellite-based risk, or is it a calm day? Mention temperature, humidity, any hazards.
# If AQI is poor, link it to urban density or industrial activity if relevant.

# ---

# 💡 **What Should Be Done**
# Give 3 specific, actionable recommendations tailored to this location and its dominant risks.
# These should be practical — for local governments, residents, farmers, or urban planners
# depending on what is relevant. NOT generic climate advice.

# ---

# RULES:
# - Total response: 350–450 words
# - Never use bullet points — use flowing prose paragraphs
# - Always name the specific zone, season, and current month
# - Cross-reference all three data sources in your analysis
# - If a risk component is genuinely low, say so and explain why — don't pad with fake threats
# - Write as an expert explaining to a policymaker, not a chatbot summarising numbers"""


# # ================================================================
# # GEMINI AGENT (free tier)
# # ================================================================

# # Gemini tool schema format
# GEMINI_TOOLS = [
#     {
#         "name": "get_crii_data",
#         "description": "Retrieve satellite-derived CRII scores for a lat/lon location. Returns CRII score, risk category, agro zone, uncertainty, and component scores (flood, heat, vegetation, urban, rainfall).",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "lat": {"type": "number", "description": "Latitude"},
#                 "lon": {"type": "number", "description": "Longitude"},
#             },
#             "required": ["lat", "lon"],
#         },
#     },
#     {
#         "name": "get_live_weather",
#         "description": "Fetch real-time weather and AQI. Returns temperature, humidity, wind, active hazard flags, AQI.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "lat": {"type": "number", "description": "Latitude"},
#                 "lon": {"type": "number", "description": "Longitude"},
#             },
#             "required": ["lat", "lon"],
#         },
#     },
#     {
#         "name": "get_risk_context",
#         "description": "Get domain knowledge about an Indian agro-climatic zone and current season. Returns typical hazards, monsoon timing, seasonal risk status, and important domain notes.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "agro_zone": {"type": "string", "description": "Agro-climatic zone name from get_crii_data"},
#                 "month":     {"type": "integer", "description": "Current month (1–12)"},
#             },
#             "required": ["agro_zone", "month"],
#         },
#     },
# ]

# def run_gemini_agent(place_name: str, lat: float, lon: float) -> str:
#     """Run the CRII agent using Google Gemini 2.0 Flash (free tier)."""
#     try:
#         import google.generativeai as genai
#     except ImportError:
#         return (
#             "⚠️ google-generativeai not installed.\n"
#             "Run: pip install google-generativeai\n"
#             "Then get a free key at: https://aistudio.google.com/apikey"
#         )

#     api_key = os.environ.get("GEMINI_API_KEY")
#     if not api_key:
#         return (
#             "⚠️ GEMINI_API_KEY not set.\n"
#             "Get your free key at https://aistudio.google.com/apikey\n"
#             "Then run: set GEMINI_API_KEY=your_key (Windows)"
#         )

#     genai.configure(api_key=api_key)

#     # Define tools for Gemini
#     tools = [genai.protos.Tool(
#         function_declarations=[
#             genai.protos.FunctionDeclaration(**t) for t in GEMINI_TOOLS
#         ]
#     )]

#     model = genai.GenerativeModel(
#         model_name="gemini-2.0-flash",
#         system_instruction=SYSTEM_PROMPT,
#         tools=tools,
#     )

#     month = datetime.datetime.now().month
#     chat  = model.start_chat()

#     user_message = (
#         f"Analyze the climate risk for {place_name}, India. "
#         f"Coordinates: lat={lat}, lon={lon}. Current month: {month}. "
#         f"Call all three tools, then give me a complete risk assessment."
#     )

#     response = chat.send_message(user_message)

#     # Agentic loop
#     max_iterations = 6
#     for _ in range(max_iterations):
#         # Collect all function calls in this response
#         calls = [
#             part.function_call
#             for candidate in response.candidates
#             for part in candidate.content.parts
#             if part.function_call.name
#         ]

#         if not calls:
#             # No more tool calls — extract and return text
#             texts = [
#                 part.text
#                 for candidate in response.candidates
#                 for part in candidate.content.parts
#                 if hasattr(part, "text") and part.text
#             ]
#             return "\n".join(texts) if texts else "⚠️ Agent returned no text response."

#         # Execute all tool calls and send results back
#         tool_responses = []
#         for call in calls:
#             result = dispatch_tool(call.name, dict(call.args))
#             tool_responses.append(
#                 genai.protos.Part(
#                     function_response=genai.protos.FunctionResponse(
#                         name=call.name,
#                         response={"result": result}
#                     )
#                 )
#             )

#         response = chat.send_message(tool_responses)

#     return "⚠️ Agent did not complete within iteration limit. Please try again."


# # ================================================================
# # CLAUDE AGENT (paid — better quality)
# # ================================================================

# CLAUDE_TOOLS = [
#     {
#         "name": "get_crii_data",
#         "description": "Retrieve satellite-derived CRII scores for a lat/lon location.",
#         "input_schema": {
#             "type": "object",
#             "properties": {
#                 "lat": {"type": "number", "description": "Latitude"},
#                 "lon": {"type": "number", "description": "Longitude"},
#             },
#             "required": ["lat", "lon"],
#         },
#     },
#     {
#         "name": "get_live_weather",
#         "description": "Fetch real-time weather and AQI for a location.",
#         "input_schema": {
#             "type": "object",
#             "properties": {
#                 "lat": {"type": "number", "description": "Latitude"},
#                 "lon": {"type": "number", "description": "Longitude"},
#             },
#             "required": ["lat", "lon"],
#         },
#     },
#     {
#         "name": "get_risk_context",
#         "description": "Get domain knowledge about an Indian agro-climatic zone and current season.",
#         "input_schema": {
#             "type": "object",
#             "properties": {
#                 "agro_zone": {"type": "string", "description": "Agro-climatic zone from get_crii_data"},
#                 "month":     {"type": "integer", "description": "Current month (1–12)"},
#             },
#             "required": ["agro_zone", "month"],
#         },
#     },
# ]

# def run_claude_agent(place_name: str, lat: float, lon: float) -> str:
#     """Run the CRII agent using Anthropic Claude Haiku (paid, better quality)."""
#     try:
#         import anthropic
#     except ImportError:
#         return "⚠️ anthropic not installed. Run: pip install anthropic"

#     api_key = os.environ.get("ANTHROPIC_API_KEY")
#     if not api_key:
#         return "⚠️ ANTHROPIC_API_KEY not set."

#     client   = anthropic.Anthropic(api_key=api_key)
#     month    = datetime.datetime.now().month
#     messages = [{
#         "role": "user",
#         "content": (
#             f"Analyze the climate risk for {place_name}, India. "
#             f"Coordinates: lat={lat}, lon={lon}. Current month: {month}. "
#             f"Use all three tools, then give me a complete risk assessment."
#         )
#     }]

#     for _ in range(6):
#         response = client.messages.create(
#             model="claude-haiku-4-5-20251001",
#             max_tokens=1024,
#             system=SYSTEM_PROMPT,
#             tools=CLAUDE_TOOLS,
#             messages=messages,
#         )

#         if response.stop_reason == "end_turn":
#             return "\n".join(
#                 b.text for b in response.content if hasattr(b, "text")
#             )

#         if response.stop_reason == "tool_use":
#             messages.append({"role": "assistant", "content": response.content})
#             results = []
#             for b in response.content:
#                 if b.type == "tool_use":
#                     results.append({
#                         "type":        "tool_result",
#                         "tool_use_id": b.id,
#                         "content":     dispatch_tool(b.name, b.input),
#                     })
#             messages.append({"role": "user", "content": results})

#     return "⚠️ Agent did not complete within iteration limit."


# # ================================================================
# # PUBLIC ENTRY POINT
# # Called from app.py — routes to Gemini or Claude based on USE_GEMINI flag
# # ================================================================

# def run_crii_agent(place_name: str, lat: float, lon: float) -> str:
#     if USE_GEMINI:
#         return run_gemini_agent(place_name, lat, lon)
#     else:
#         return run_claude_agent(place_name, lat, lon)












# crii_agent/crii_agent.py

import os
import json
import datetime
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# LOAD DATA ONCE (module-level cache)
# -----------------------------
_crii_df = None
_grid_df = None

def _load_data():
    global _crii_df, _grid_df
    if _crii_df is None:
        _crii_df = pd.read_csv("data/india_crii_results.csv")
        _grid_df = pd.read_csv("data/india_grid.csv")

# ================================================================
# TOOL FUNCTIONS
# ================================================================

def get_crii_data(lat: float, lon: float) -> dict:
    _load_data()
    match = _grid_df[
        (_grid_df["lat_min"] <= lat) & (lat <= _grid_df["lat_max"]) &
        (_grid_df["lon_min"] <= lon) & (lon <= _grid_df["lon_max"])
    ]
    if len(match) == 0:
        return {"error": "Location outside India study area"}

    grid_id = int(match.iloc[0]["grid_id"])
    rows = _crii_df[_crii_df["grid_id"] == grid_id]

    if len(rows) == 0:
        return {"error": f"No CRII data for grid_id {grid_id}"}

    row = rows.iloc[0]

    return {
        "grid_id": grid_id,
        "crii_score": round(float(row["crii"]), 3),
        "uncertainty": round(float(row.get("crii_uncertainty", 0.05)), 3),
        "risk_category": str(row["risk_category"]),
        "agro_zone": str(row.get("agro_zone", "Unknown")),
        "components": {
            "flood_norm": float(row["flood_norm"]),
            "lst_norm": float(row["lst_norm"]),
            "veg_norm": float(row["veg_norm"]),
            "urban_norm": float(row["urban_norm"]),
            "rainfall_norm": float(row["rainfall_norm"]),
        }
    }

OWM_API_KEY = "029a4bf0e7246078162240bee9931c35"

def get_live_weather(lat: float, lon: float) -> dict:
    result = {}
    try:
        res = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric",
            timeout=8
        ).json()

        if "main" in res:
            result["weather"] = {
                "temperature_c": res["main"]["temp"],
                "humidity_pct": res["main"]["humidity"],
                "wind_ms": res["wind"]["speed"],
                "condition": res["weather"][0]["description"],
            }
    except Exception as e:
        result["weather_error"] = str(e)

    return result

def get_risk_context(agro_zone: str, month: int) -> dict:
    season = (
        "winter" if month in [12,1,2] else
        "pre_monsoon" if month in [3,4,5] else
        "monsoon" if month in [6,7,8,9] else
        "post_monsoon"
    )

    return {
        "agro_zone": agro_zone,
        "season": season,
    }

# ================================================================
# TOOL DISPATCH
# ================================================================

TOOL_MAP = {
    "get_crii_data": get_crii_data,
    "get_live_weather": get_live_weather,
    "get_risk_context": get_risk_context,
}

def dispatch_tool(name: str, args: dict) -> str:
    fn = TOOL_MAP.get(name)
    if fn is None:
        return json.dumps({"error": "Unknown tool"})
    return json.dumps(fn(**args))

# ================================================================
# SYSTEM PROMPT
# ================================================================

SYSTEM_PROMPT = """You are CRII-Agent, an expert climate risk analyst for India.

You MUST:
1. Call get_crii_data
2. Call get_risk_context
3. Call get_live_weather

Then generate a structured climate risk report.
"""

# ================================================================
# GEMINI AGENT (FULLY FUNCTIONAL)
# ================================================================

def run_crii_agent(place_name: str, lat: float, lon: float) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        return "⚠️ Install: pip install google-generativeai"

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ GEMINI_API_KEY not set"

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT
    )

    month = datetime.datetime.now().month

    # Initial message
    response = model.generate_content(
        f"""
        Analyze climate risk for {place_name}, India.
        lat={lat}, lon={lon}, month={month}

        Use tools.
        """
    )

    # 🔁 Manual tool execution loop
    for _ in range(5):
        text = response.text if hasattr(response, "text") else ""

        if "get_crii_data" in text:
            data = get_crii_data(lat, lon)
            response = model.generate_content(f"{text}\nDATA:\n{data}")
            continue

        if "get_risk_context" in text:
            zone = data.get("agro_zone", "Unknown")
            context = get_risk_context(zone, month)
            response = model.generate_content(f"{text}\nCONTEXT:\n{context}")
            continue

        if "get_live_weather" in text:
            weather = get_live_weather(lat, lon)
            response = model.generate_content(f"{text}\nWEATHER:\n{weather}")
            continue

        return text

    return "⚠️ Agent failed"