import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Load all datasets
ndvi_df = pd.read_csv("data/grid_ndvi.csv")
lst_df = pd.read_csv("data/grid_lst.csv")
urban_df = pd.read_csv("data/grid_urban.csv")
flood_df = pd.read_csv("data/grid_flood.csv")

# Merge all on grid_id
df = ndvi_df.merge(lst_df, on="grid_id") \
            .merge(urban_df, on="grid_id") \
            .merge(flood_df, on="grid_id")

# Handle missing values
df = df.dropna()

# Convert NDVI to stress (LOW NDVI = HIGH stress)
df["vegetation_stress"] = 1 - df["ndvi"]

# Normalize all indicators
scaler = MinMaxScaler()

df[["flood_norm", "lst_norm", "veg_norm", "urban_norm"]] = scaler.fit_transform(
    df[["flood", "lst", "vegetation_stress", "urban"]]
)

# Compute CRII (equal weights)
df["crii"] = (
    0.25 * df["flood_norm"] +
    0.25 * df["lst_norm"] +
    0.25 * df["veg_norm"] +
    0.25 * df["urban_norm"]
)

# Risk classification
def classify(crii):
    if crii < 0.25:
        return "Low"
    elif crii < 0.5:
        return "Moderate"
    elif crii < 0.75:
        return "High"
    else:
        return "Critical"

df["risk_category"] = df["crii"].apply(classify)

# Save result
df.to_csv("data/crii_results.csv", index=False)

print("CRII computation completed")