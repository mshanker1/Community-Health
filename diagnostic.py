import pandas as pd

df = pd.read_csv("RVN-3.csv")

print("Data types before cleaning:")
print(df.dtypes.head(10))

print("\nSample values from problematic columns:")
# Check the first few metric columns for mixed types
for col in df.columns[3:8]:  # Skip FIPS, State, County
    print(f"\n{col}:")
    print(f"  Type: {df[col].dtype}")
    unique_vals = df[col].dropna().unique()
    if len(unique_vals) > 0:
        print(f"  Sample values: {unique_vals[:5]}")
        print(f"  Non-numeric values:", [v for v in unique_vals[:10] if not str(v).replace('.','').replace('-','').isdigit()])