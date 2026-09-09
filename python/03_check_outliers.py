from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "python" / "raw"

files = [
    RAW_DIR / "2024" / "yellow_tripdata_2024-01.parquet",
    RAW_DIR / "2024" / "yellow_tripdata_2024-02.parquet",
    RAW_DIR / "2025" / "yellow_tripdata_2025-01.parquet",
    RAW_DIR / "2025" / "yellow_tripdata_2025-02.parquet"
]

for file in files:

    print("\n" + "=" * 60)
    print(file.name)
    print("=" * 60)

    df = pd.read_parquet(file)

    pickup = pd.to_datetime(df["tpep_pickup_datetime"])
    dropoff = pd.to_datetime(df["tpep_dropoff_datetime"])

    duration = (dropoff - pickup).dt.total_seconds() / 60

    print("\nTrip Distance Percentiles")
    print(df["trip_distance"].quantile([0.50, 0.90, 0.95, 0.99, 0.999]))

    print("\nFare Percentiles")
    print(df["fare_amount"].quantile([0.50, 0.90, 0.95, 0.99, 0.999]))

    print("\nTrip Duration Percentiles")
    print(duration.quantile([0.50, 0.90, 0.95, 0.99, 0.999]))

    print("\nPassenger Count")
    print(df["passenger_count"].value_counts(dropna=False).sort_index())

    print("\nAverage Speed Percentiles")

    valid_duration = duration > 0

    speed = df.loc[valid_duration, "trip_distance"] / (
        duration[valid_duration] / 60
    )

    print(speed.quantile([0.50, 0.90, 0.95, 0.99, 0.999]))