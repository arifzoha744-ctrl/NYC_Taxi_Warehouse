from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "python" / "raw"

zone_file = RAW_DIR / "taxi_zone_lookup.csv"

zones = pd.read_csv(zone_file)
zones.columns = zones.columns.str.strip()

print("Taxi Zone Lookup Columns:")
print(zones.columns.tolist())

valid_zone_ids = set(zones["LocationID"].dropna().astype(int))

files = [
    RAW_DIR / "2024" / "yellow_tripdata_2024-01.parquet",
    RAW_DIR / "2024" / "yellow_tripdata_2024-02.parquet",
    RAW_DIR / "2025" / "yellow_tripdata_2025-01.parquet",
    RAW_DIR / "2025" / "yellow_tripdata_2025-02.parquet"
]

for file in files:

    print("\n" + "=" * 60)
    print(f"Checking zones: {file.name}")
    print("=" * 60)

    df = pd.read_parquet(file)

    pickup_ids = set(df["PULocationID"].dropna().astype(int))
    dropoff_ids = set(df["DOLocationID"].dropna().astype(int))

    unknown_pickup = pickup_ids - valid_zone_ids
    unknown_dropoff = dropoff_ids - valid_zone_ids

    print("Unique pickup zones:", len(pickup_ids))
    print("Unique drop-off zones:", len(dropoff_ids))
    print("Unknown pickup zone IDs:", sorted(unknown_pickup))
    print("Unknown drop-off zone IDs:", sorted(unknown_dropoff))
    print("Number of unknown pickup zones:", len(unknown_pickup))
    print("Number of unknown drop-off zones:", len(unknown_dropoff))