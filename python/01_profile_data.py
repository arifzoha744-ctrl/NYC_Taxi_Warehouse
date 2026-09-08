from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

files = [
    RAW_DIR / "2024" / "yellow_tripdata_2024-01.parquet",
    RAW_DIR / "2024" / "yellow_tripdata_2024-02.parquet",
    RAW_DIR / "2025" / "yellow_tripdata_2025-01.parquet",
    RAW_DIR / "2025" / "yellow_tripdata_2025-02.parquet"
]

results = []

for file in files:
    print(f"\nReading: {file.name}")

    df = pd.read_parquet(file)

    null_counts = df.isnull().sum().to_dict()

    result = {
        "SourceFile": file.name,
        "Rows": len(df),
        "Columns": len(df.columns),
        "ColumnNames": ", ".join(df.columns),
        "DataTypes": ", ".join(
            f"{col}:{dtype}" for col, dtype in df.dtypes.items()
        ),
        "DuplicateRows": int(df.duplicated().sum()),
        "MinPickupDate": df["tpep_pickup_datetime"].min(),
        "MaxPickupDate": df["tpep_pickup_datetime"].max(),
        "MinTripDistance": df["trip_distance"].min(),
        "MaxTripDistance": df["trip_distance"].max(),
        "MinFare": df["fare_amount"].min(),
        "MaxFare": df["fare_amount"].max(),
        "MinTotalAmount": df["total_amount"].min(),
        "MaxTotalAmount": df["total_amount"].max(),
        "UniquePickupLocations": df["PULocationID"].nunique(),
        "UniqueDropoffLocations": df["DOLocationID"].nunique(),
        "FileSizeMB": round(file.stat().st_size / (1024 * 1024), 2),
        "NullCounts": str(null_counts)
    }

    results.append(result)

    print(f"Rows: {result['Rows']}")
    print(f"Columns: {result['Columns']}")
    print(f"Duplicates: {result['DuplicateRows']}")
    print(f"Pickup date: {result['MinPickupDate']} → {result['MaxPickupDate']}")

report = pd.DataFrame(results)

output_file = REPORT_DIR / "Data_Profiling_Report.csv"
report.to_csv(output_file, index=False)

print("\n===================================")
print("Profiling completed successfully.")
print(f"Report saved to: {output_file}")
print("===================================")