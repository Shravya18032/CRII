# 🌍 Climate Risk Intelligence System (CRII)

A geospatial intelligence system that analyzes climate risks across India using satellite data, environmental indicators, and real-time weather integration.

---

## 🚀 Project Overview

The **Climate Risk Intelligence System (CRII)** is designed to:

* Analyze environmental stress across regions in India
* Compute a **Climate Risk Score (CRII)** using multiple geospatial factors
* Provide **location-based risk classification and threat diagnosis**
* Integrate **real-time weather and air quality data** for enhanced insights

---

## 🧠 Key Features

* 📍 Location-based analysis (any place in India)
* 🛰 Satellite data integration using Google Earth Engine
* 📊 Multi-factor risk computation:

  * Vegetation Health (NDVI)
  * Land Surface Temperature (LST)
  * Flood Risk (Sentinel-1)
  * Urban Stress (GHSL)
  * Rainfall (ERA5)
* 📈 Dynamic CRII scoring and classification
* 🌦 Real-time weather + AQI integration
* 🚨 Automated threat detection system

---

## 🏗️ System Architecture

```
User Input (Location)
        ↓
Geocoding (Lat/Lon)
        ↓
Grid Mapping (India Grid)
        ↓
Precomputed CRII Data
        ↓
+ Real-time Weather API
        ↓
Risk Analysis + Threat Detection
        ↓
Streamlit Dashboard Output
```

---

## 🗂️ Project Structure

```
CRII/
│
├── app.py                      # Streamlit application
│
├── data/
│   ├── india_grid.csv
│   ├── india_cleaned.csv
│   ├── india_crii_results.csv
│
├── preprocessing/
│   ├── extract_ndvi_india.py
│   ├── extract_lst_india.py
│   ├── extract_flood_india.py
│   ├── extract_rainfall_india.py
│   ├── extract_urban_india.py
│
├── crii_engine/
│   └── compute_crii_india.py
│
└── README.md
```

---

## ⚙️ Tech Stack

* **Python**
* **Streamlit** – UI Dashboard
* **Google Earth Engine (GEE)** – Satellite Data Processing
* **Pandas / Scikit-learn** – Data Processing & Normalization
* **OpenWeather API** – Real-time Weather + AQI

---

## 📊 CRII Computation

The CRII score is computed using normalized environmental factors:

```
CRII = 0.30 * Flood Risk
     + 0.25 * LST
     + 0.20 * Vegetation Stress
     + 0.15 * Urban Stress
     + 0.10 * Rainfall
```

Risk levels are classified dynamically using quantiles:

* Low
* Moderate
* High
* Critical

---

## 🛰️ Data Sources

* Sentinel-1 (Flood proxy)
* MODIS (NDVI, LST)
* ERA5 (Rainfall)
* GHSL (Urbanization)
* OpenWeather API (Weather + AQI)

---

## ▶️ How to Run the Project

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/GithubSneha2004/CRII.git
cd CRII
```

---

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

If requirements file is not available:

```bash
pip install streamlit pandas geopy requests rapidfuzz scikit-learn earthengine-api
```

---

### 3️⃣ Setup Google Earth Engine

```bash
earthengine authenticate
```

Then initialize in Python:

```python
import ee
ee.Initialize()
```

---

### 4️⃣ Run Data Preprocessing (Optional / First-time)

Run all scripts inside `/preprocessing`:

```bash
python preprocessing/extract_ndvi_india.py
python preprocessing/extract_lst_india.py
python preprocessing/extract_flood_india.py
python preprocessing/extract_rainfall_india.py
python preprocessing/extract_urban_india.py
```

---

### 5️⃣ Compute CRII

```bash
python crii_engine/compute_crii_india.py
```

---

### 6️⃣ Run the App

```bash
streamlit run app.py
```

---

## 📌 Example Output

* CRII Score (e.g., 0.22)
* Risk Level (Low / Moderate / High / Critical)
* Threat Analysis (Heat, Flood, Vegetation, Urban Stress)
* Weather Insights
* Air Quality Index

---

## ⚠️ Current Limitations

* Uses yearly averaged satellite data (no temporal dynamics yet)
* Static weights in CRII computation
* Limited contextual interpretation of threats
* Grid-based approximation (not pixel-level precision)

---

## 🚀 Future Improvements

* ⏳ Time-series analysis (seasonal CRII)
* 🧠 Context-aware threat reasoning (region-specific insights)
* 🤖 Machine learning-based weighting
* 🌐 Real-time satellite integration (GEE live queries)
* 📊 Advanced visualization (maps, graphs)

---

## 👥 Contributors

* Sneha Biradar
* Yamini K
* Shravya H

---

## 📜 License

This project is for academic and research purposes.

---

## 💡 Note

This is an evolving system aimed at building a **data-driven climate risk intelligence platform** for India.

---
