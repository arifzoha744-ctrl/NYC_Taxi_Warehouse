from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

file_2024 = RAW_DIR / "2024" / "yellow_tripdata_2024-01.parquet"
file_2025 = RAW_DIR / "2025" / "yellow_tripdata_2025-01.parquet"

print("Reading 2024 file...")
df_2024 = pd.read_parquet(file_2024)

print("Reading 2025 file...")
df_2025 = pd.read_parquet(file_2025)

columns_2024 = set(df_2024.columns)
columns_2025 = set(df_2025.columns)

common_columns = sorted(columns_2024 & columns_2025)
missing_from_2024 = sorted(columns_2025 - columns_2024)
missing_from_2025 = sorted(columns_2024 - columns_2025)

results = []

for column in sorted(columns_2024 | columns_2025):

    exists_2024 = column in columns_2024
    exists_2025 = column in columns_2025

    dtype_2024 = str(df_2024[column].dtype) if exists_2024 else "NOT PRESENT"
    dtype_2025 = str(df_2025[column].dtype) if exists_2025 else "NOT PRESENT"

    if exists_2024 and exists_2025:
        status = "Common"
    elif exists_2025:
        status = "Added in 2025"
    else:
        status = "Missing in 2025"

    if exists_2024 and exists_2025 and dtype_2024 != dtype_2025:
        type_difference = "Yes"
    else:
        type_difference = "No"

    results.append({
        "Column": column,
        "2024_Dtype": dtype_2024,
        "2025_Dtype": dtype_2025,
        "Status": status,
        "TypeDifference": type_difference
    })

report = pd.DataFrame(results)

output_file = REPORT_DIR / "Schema_Comparison.csv"
report.to_csv(output_file, index=False)

print("\n==============================")
print("SCHEMA COMPARISON COMPLETED")
print("==============================")

print("\nCommon columns:", len(common_columns))
print("Missing from 2024:", missing_from_2024)
print("Missing from 2025:", missing_from_2025)

print("\nSchema differences:")
print(report[report["Status"] != "Common"])

print(f"\nReport saved to: {output_file}")
