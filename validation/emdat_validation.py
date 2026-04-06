import pandas as pd

df = pd.read_csv("data/hybrid_crii_results.csv")

# Count categories
risk_counts = df["hybrid_risk"].value_counts()

print("Risk Distribution:")
print(risk_counts)

total = len(df)

high_ratio = risk_counts.get("High", 0) / total
critical_ratio = risk_counts.get("Critical", 0) / total
moderate_ratio = risk_counts.get("Moderate", 0) / total

print(f"\nHigh ratio: {high_ratio:.2f}")
print(f"Critical ratio: {critical_ratio:.2f}")
print(f"Moderate ratio: {moderate_ratio:.2f}")

# Validation logic
if moderate_ratio > 0.4 and (high_ratio + critical_ratio) > 0.05:
    print("\nValidation Result: Realistic risk distribution (GOOD)")
else:
    print("\nValidation Result: Distribution not realistic (Needs tuning)")

# Save
df.to_csv("data/validation_results.csv", index=False)