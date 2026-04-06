# # import pandas as pd
# # from sklearn.preprocessing import MinMaxScaler

# # # Load CLEANED dataset (IMPORTANT CHANGE)
# # df = pd.read_csv("data/india_cleaned.csv")

# # print("Data loaded:", df.shape)

# # # -----------------------------
# # # STEP 1 — Feature Engineering
# # # -----------------------------

# # # Vegetation stress (low NDVI = high stress)
# # df["vegetation_stress"] = 1 - df["ndvi"]

# # # -----------------------------
# # # STEP 2 — Normalization
# # # -----------------------------

# # scaler = MinMaxScaler()

# # df[["flood_norm", "lst_norm", "veg_norm", "urban_norm"]] = scaler.fit_transform(
# #     df[["flood", "lst", "vegetation_stress", "urban"]]
# # )

# # print("Normalization completed")

# # # -----------------------------
# # # STEP 3 — CRII Computation
# # # -----------------------------

# # df["crii"] = (
# #     0.25 * df["flood_norm"] +
# #     0.25 * df["lst_norm"] +
# #     0.25 * df["veg_norm"] +
# #     0.25 * df["urban_norm"]
# # )

# # print("CRII calculated")

# # # -----------------------------
# # # STEP 4 — Classification
# # # -----------------------------

# # def classify(val):
# #     if val < 0.25:
# #         return "Low"
# #     elif val < 0.5:
# #         return "Moderate"
# #     elif val < 0.75:
# #         return "High"
# #     else:
# #         return "Critical"

# # df["risk_category"] = df["crii"].apply(classify)

# # print("Classification completed")

# # # -----------------------------
# # # STEP 5 — Save Results
# # # -----------------------------

# # df.to_csv("data/india_crii_results.csv", index=False)

# # print("India CRII computation completed ✅")


# import pandas as pd
# from sklearn.preprocessing import MinMaxScaler

# # -----------------------------
# # STEP 0 — Load Data
# # -----------------------------
# df = pd.read_csv("data/india_cleaned.csv")

# print("Data loaded:", df.shape)
# def apply_geographic_correction(lat, row):
    
#     # Himalaya region (very rough)
#     if lat > 28:
#         row["urban_norm"] *= 0.2   # reduce urban effect
#         row["lst_norm"] *= 0.5     # reduce heat effect

#     # Coastal regions (flood prone)
#     if 8 < lat < 22:
#         row["flood_norm"] *= 1.2

#     return row
# # -----------------------------
# # STEP 1 — Handle Missing Values (CRITICAL FIX)
# # -----------------------------
# # Fill missing values with column mean
# df["ndvi"] = df["ndvi"].fillna(df["ndvi"].mean())
# df["lst"] = df["lst"].fillna(df["lst"].mean())
# df["urban"] = df["urban"].fillna(df["urban"].mean())
# df["flood"] = df["flood"].fillna(df["flood"].mean())

# print("Missing values handled")

# # -----------------------------
# # STEP 2 — Feature Engineering
# # -----------------------------
# # Vegetation stress (low NDVI = high stress)
# df["vegetation_stress"] = 1 - df["ndvi"]

# # -----------------------------
# # STEP 3 — Normalization
# # -----------------------------
# scaler = MinMaxScaler()

# features = ["flood", "lst", "vegetation_stress", "urban"]

# df[["flood_norm", "lst_norm", "veg_norm", "urban_norm"]] = scaler.fit_transform(
#     df[features]
# )

# print("Normalization completed")

# # -----------------------------
# # STEP 4 — CRII Computation
# # -----------------------------
# df["crii"] = (
#     0.25 * df["flood_norm"] +
#     0.25 * df["lst_norm"] +
#     0.25 * df["veg_norm"] +
#     0.25 * df["urban_norm"]
# )

# # 🔧 Extra safety (VERY IMPORTANT)
# df["crii"] = df["crii"].fillna(df["crii"].mean())

# print("CRII calculated")

# # -----------------------------
# # STEP 5 — Classification
# # -----------------------------
# def classify(val):
#     if val < 0.25:
#         return "Low"
#     elif val < 0.5:
#         return "Moderate"
#     elif val < 0.75:
#         return "High"
#     else:
#         return "Critical"

# df["risk_category"] = df["crii"].apply(classify)

# print("Classification completed")

# # -----------------------------
# # STEP 6 — Save Results
# # -----------------------------
# df.to_csv("data/india_crii_results.csv", index=False)
# print("NaN count in CRII:", df["crii"].isna().sum())
# print("India CRII computation completed ✅")




# import pandas as pd
# from sklearn.preprocessing import MinMaxScaler

# # -----------------------------
# # STEP 0 — Load Data
# # -----------------------------
# df = pd.read_csv("data/india_cleaned.csv")

# print("Data loaded:", df.shape)

# # -----------------------------
# # STEP 1 — Feature Engineering
# # -----------------------------
# df["vegetation_stress"] = 1 - df["ndvi"]

# # -----------------------------
# # STEP 2 — Normalization
# # -----------------------------
# scaler = MinMaxScaler()

# features = ["flood", "lst", "vegetation_stress", "urban", "rainfall"]

# df[["flood_norm", "lst_norm", "veg_norm", "urban_norm", "rainfall_norm"]] = scaler.fit_transform(
#     df[features]
# )

# print("Normalization completed")

# # -----------------------------
# # STEP 3 — CRII Computation (UPDATED)
# # -----------------------------
# df["crii"] = (
#     0.30 * df["flood_norm"] +
#     0.25 * df["lst_norm"] +
#     0.20 * df["veg_norm"] +
#     0.15 * df["urban_norm"] +
#     0.10 * df["rainfall_norm"]
# )

# # Safety
# df["crii"] = df["crii"].fillna(df["crii"].mean())

# print("CRII calculated")

# # -----------------------------
# # STEP 4 — Dynamic Classification (NEW 🔥)
# # -----------------------------
# q1 = df["crii"].quantile(0.25)
# q2 = df["crii"].quantile(0.50)
# q3 = df["crii"].quantile(0.75)

# def classify(val):
#     if val < q1:
#         return "Low"
#     elif val < q2:
#         return "Moderate"
#     elif val < q3:
#         return "High"
#     else:
#         return "Critical"

# df["risk_category"] = df["crii"].apply(classify)

# print("Classification completed")

# # -----------------------------
# # STEP 5 — Save
# # -----------------------------
# df.to_csv("data/india_crii_results.csv", index=False)

# print("NaN count in CRII:", df["crii"].isna().sum())
# print("India CRII computation completed ✅")

#crii_engine/compute_crii_india.py
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("data/india_cleaned.csv")

print("Data loaded:", df.shape)

# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
df["vegetation_stress"] = 1 - df["ndvi"]

# -----------------------------
# NORMALIZATION
# -----------------------------
scaler = MinMaxScaler()

features = ["flood", "lst", "vegetation_stress", "urban", "rainfall"]

df[["flood_norm", "lst_norm", "veg_norm", "urban_norm", "rainfall_norm"]] = scaler.fit_transform(
    df[features]
)

print("Normalization completed")

# -----------------------------
# GEOGRAPHIC CORRECTION (NEW 🔥)
# -----------------------------
def apply_geo_correction(row):
    lat = (row["lat_min"] + row["lat_max"]) / 2

    # Himalaya region
    if lat > 28:
        row["lst_norm"] *= 0.5
        row["urban_norm"] *= 0.3

    # Coastal regions
    if 8 < lat < 22:
        row["flood_norm"] *= 1.2

    # Highly urban areas
    if row["urban_norm"] > 0.6:
        row["urban_norm"] *= 1.2

    return row

df = df.apply(apply_geo_correction, axis=1)

print("Geographic correction applied")

# -----------------------------
# CRII COMPUTATION (UPDATED)
# -----------------------------
df["crii"] = (
    0.30 * df["flood_norm"] +
    0.25 * df["lst_norm"] +
    0.20 * df["veg_norm"] +
    0.15 * df["urban_norm"] +
    0.10 * df["rainfall_norm"]
)

df["crii"] = df["crii"].fillna(df["crii"].mean())

print("CRII calculated")

# -----------------------------
# DYNAMIC CLASSIFICATION
# -----------------------------
q1 = df["crii"].quantile(0.25)
q2 = df["crii"].quantile(0.50)
q3 = df["crii"].quantile(0.75)

def classify(val):
    if val < q1:
        return "Low"
    elif val < q2:
        return "Moderate"
    elif val < q3:
        return "High"
    else:
        return "Critical"

df["risk_category"] = df["crii"].apply(classify)

print("Classification completed")

# -----------------------------
# SAVE
# -----------------------------
df.to_csv("data/india_crii_results.csv", index=False)

print("India CRII computation completed ✅")