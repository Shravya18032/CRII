import pandas as pd

# Load datasets
ndvi = pd.read_csv("data/india_ndvi.csv")
lst = pd.read_csv("data/india_lst.csv")
urban = pd.read_csv("data/india_urban.csv")
flood = pd.read_csv("data/india_flood.csv")
rainfall = pd.read_csv("data/india_rainfall.csv")   # NEW
grid = pd.read_csv("data/india_grid.csv")

# Convert to numeric
for df in [ndvi, lst, urban, flood, rainfall]:
    for col in df.columns:
        if col != "grid_id":
            df[col] = pd.to_numeric(df[col], errors="coerce")

# Merge ALL (outer join)
df = grid.merge(ndvi, on="grid_id", how="left") \
         .merge(lst, on="grid_id", how="left") \
         .merge(urban, on="grid_id", how="left") \
         .merge(flood, on="grid_id", how="left") \
         .merge(rainfall, on="grid_id", how="left")

print("After merge:")
print(df.isna().sum())

# -----------------------------
# SMART FILLING
# -----------------------------

df["ndvi"] = df["ndvi"].fillna(df["ndvi"].mean())
df["lst"] = df["lst"].fillna(df["lst"].mean())
df["urban"] = df["urban"].fillna(df["urban"].mean())
df["flood"] = df["flood"].fillna(df["flood"].mean())
df["rainfall"] = df["rainfall"].fillna(df["rainfall"].mean())  # NEW

# Final safety
df = df.fillna(0)

print("After cleaning:")
print(df.isna().sum())

# Save
df.to_csv("data/india_cleaned.csv", index=False)

print("Data cleaning with rainfall completed ✅")