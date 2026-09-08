from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

zones = pd.read_csv(RAW_DIR / "taxi_zone_lookup.csv")
zones.columns = zones.columns.str.strip()
valid_zone_ids = set(zones["LocationID"].dropna().astype(int))

files = [
    RAW_DIR / "2024" / "yellow_tripdata_2024-01.parquet",
    RAW_DIR / "2024" / "yellow_tripdata_2024-02.parquet",
    RAW_DIR / "2025" / "yellow_tripdata_2025-01.parquet",
    RAW_DIR / "2025" / "yellow_tripdata_2025-02.parquet"
]

reconciliation = []
quarantine_records = []

for file in files:

    print("\n" + "=" * 60)
    print(file.name)
    print("=" * 60)

    df = pd.read_parquet(file)

    pickup = pd.to_datetime(df["tpep_pickup_datetime"])
    dropoff = pd.to_datetime(df["tpep_dropoff_datetime"])

    duration = (dropoff - pickup).dt.total_seconds() / 60

    speed = df["trip_distance"].div(duration / 60)
    speed = speed.where(duration > 0)

    invalid_date = pickup > dropoff
    invalid_duration = duration <= 0
    negative_distance = df["trip_distance"] < 0
    high_fare = df["fare_amount"] > 500
    high_distance = df["trip_distance"] > 100
    long_duration = duration > 300
    high_speed = speed > 100
    unknown_pickup = ~df["PULocationID"].isin(valid_zone_ids)
    unknown_dropoff = ~df["DOLocationID"].isin(valid_zone_ids)

    issue_mask = (
        invalid_date
        | invalid_duration
        | negative_distance
        | high_fare
        | high_distance
        | long_duration
        | high_speed
        | unknown_pickup
        | unknown_dropoff
    )

    duplicate_key = pd.util.hash_pandas_object(
        df[
            [
                "VendorID",
                "tpep_pickup_datetime",
                "tpep_dropoff_datetime",
                "passenger_count",
                "trip_distance",
                "PULocationID",
                "DOLocationID",
                "fare_amount",
                "total_amount"
            ]
        ],
        index=False
    )

    duplicate_mask = duplicate_key.duplicated(keep="first")

    quarantine_mask = issue_mask | duplicate_mask
    valid_mask = ~quarantine_mask

    reason_codes = pd.Series("", index=df.index, dtype="object")
    reason_descriptions = pd.Series("", index=df.index, dtype="object")

    reason_codes.loc[invalid_date] += "INVALID_DATE|"
    reason_descriptions.loc[invalid_date] += "Pickup time is after drop-off time|"

    reason_codes.loc[invalid_duration] += "INVALID_DURATION|"
    reason_descriptions.loc[invalid_duration] += "Trip duration is zero or negative|"

    reason_codes.loc[negative_distance] += "INVALID_DISTANCE|"
    reason_descriptions.loc[negative_distance] += "Trip distance is negative|"

    reason_codes.loc[high_fare] += "HIGH_FARE|"
    reason_descriptions.loc[high_fare] += "Fare amount is above 500|"

    reason_codes.loc[high_distance] += "HIGH_DISTANCE|"
    reason_descriptions.loc[high_distance] += "Trip distance is above 100 miles|"

    reason_codes.loc[long_duration] += "LONG_DURATION|"
    reason_descriptions.loc[long_duration] += "Trip duration is above 300 minutes|"

    reason_codes.loc[high_speed] += "HIGH_SPEED|"
    reason_descriptions.loc[high_speed] += "Average speed is above 100 MPH|"

    reason_codes.loc[unknown_pickup] += "UNKNOWN_PICKUP_ZONE|"
    reason_descriptions.loc[unknown_pickup] += "Pickup zone not found in lookup|"

    reason_codes.loc[unknown_dropoff] += "UNKNOWN_DROPOFF_ZONE|"
    reason_descriptions.loc[unknown_dropoff] += "Drop-off zone not found in lookup|"

    reason_codes.loc[duplicate_mask] += "DUPLICATE_RECORD|"
    reason_descriptions.loc[duplicate_mask] += "Duplicate deterministic hash|"

    reason_codes = reason_codes.str.rstrip("|")
    reason_descriptions = reason_descriptions.str.rstrip("|")

    source_columns = [
        "VendorID",
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "PULocationID",
        "DOLocationID",
        "fare_amount",
        "total_amount"
    ]

    original_information = (
        df[source_columns]
        .fillna("<NULL>")
        .astype(str)
        .agg("|".join, axis=1)
    )

    quarantine_output = pd.DataFrame({
        "SourceFile": file.name,
        "ReasonCode": reason_codes.loc[quarantine_mask].values,
        "ReasonDescription": reason_descriptions.loc[quarantine_mask].values,
        "LoadRunID": f"RUN_{file.stem}",
        "OriginalRecordInformation": original_information.loc[quarantine_mask].values,
        "RecordHash": duplicate_key.loc[quarantine_mask].astype(str).values
    })

    quarantine_records.append(quarantine_output)

    raw_rows = len(df)
    valid_rows = int(valid_mask.sum())
    quarantined_rows = int(quarantine_mask.sum())
    duplicate_rows = int(duplicate_mask.sum())

    reconciliation.append({
        "SourceFile": file.name,
        "RawRows": raw_rows,
        "ValidRows": valid_rows,
        "QuarantinedRows": quarantined_rows,
        "DuplicateRows": duplicate_rows,
        "RawTotalAmount": df["total_amount"].sum(),
        "ValidTotalAmount": df.loc[valid_mask, "total_amount"].sum(),
        "QuarantinedTotalAmount": df.loc[quarantine_mask, "total_amount"].sum(),
        "Reconciles": raw_rows == valid_rows + quarantined_rows
    })

    print("Raw rows:", raw_rows)
    print("Valid rows:", valid_rows)
    print("Quarantined rows:", quarantined_rows)
    print("Duplicate rows:", duplicate_rows)

pd.DataFrame(reconciliation).to_csv(
    REPORT_DIR / "Reconciliation_Report.csv",
    index=False
)

pd.concat(quarantine_records, ignore_index=True).to_csv(
    REPORT_DIR / "Quarantine_Report.csv",
    index=False
)

print("\nValidation completed.")
print("Reconciliation report saved.")
print("Quarantine report saved.")