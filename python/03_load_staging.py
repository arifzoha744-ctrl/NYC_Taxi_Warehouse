from pathlib import Path
import pandas as pd
import pyodbc
import time

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"

file = RAW_DIR / "2025" / "yellow_tripdata_2025-02.parquet"

server = r"."
database = "NYCTaxiWarehouse"

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

start_time = time.time()

print("Reading January 2024...")
df = pd.read_parquet(file)

print("Rows read:", len(df))

df = df.rename(columns={
    "Airport_fee": "airport_fee"
})

if "cbd_congestion_fee" not in df.columns:
    df["cbd_congestion_fee"] = None

df["SourceFile"] = file.name

columns = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "RatecodeID",
    "store_and_fwd_flag",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "improvement_surcharge",
    "total_amount",
    "congestion_surcharge",
    "airport_fee",
    "cbd_congestion_fee",
    "SourceFile"
]

df = df[columns]

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO etl.LoadRun
    (
        SourceFile,
        StartTime,
        RowsRead,
        RowsLoaded,
        RowsQuarantined,
        DuplicateRows,
        Status
    )
    VALUES (?, GETDATE(), ?, 0, 0, 0, 'Running')
    """,
    file.name,
    len(df)
)

conn.commit()

cursor.execute(
    """
    SELECT TOP 1 LoadRunID
    FROM etl.LoadRun
    WHERE SourceFile = ?
    ORDER BY LoadRunID DESC
    """,
    file.name
)

load_run_id = int(cursor.fetchone()[0])

print("LoadRunID:", load_run_id)
print("Loading into SQL Server...")

insert_sql = """
INSERT INTO stg.YellowTaxiTrips
(
    VendorID,
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    passenger_count,
    trip_distance,
    RatecodeID,
    store_and_fwd_flag,
    PULocationID,
    DOLocationID,
    payment_type,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    congestion_surcharge,
    airport_fee,
    cbd_congestion_fee,
    SourceFile,
    LoadRunID
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

batch_size = 5000
rows_loaded = 0

cursor.fast_executemany = True

for start in range(0, len(df), batch_size):

    end = min(start + batch_size, len(df))

    batch = df.iloc[start:end].copy()

    batch["LoadRunID"] = load_run_id

    batch = batch.astype(object)
    batch = batch.where(pd.notna(batch), None)

    data = list(
        batch.itertuples(index=False, name=None)
    )

    cursor.executemany(insert_sql, data)
    conn.commit()

    rows_loaded += len(data)

    print(f"Loaded {rows_loaded:,} / {len(df):,} rows")

cursor.execute(
    """
    UPDATE etl.LoadRun
    SET
        RowsLoaded = ?,
        EndTime = GETDATE(),
        Status = 'Success'
    WHERE LoadRunID = ?
    """,
    rows_loaded,
    load_run_id
)

conn.commit()

cursor.close()
conn.close()

elapsed = time.time() - start_time

print("Rows loaded:", rows_loaded)
print("Load completed successfully.")
print("Time:", round(elapsed, 2), "seconds")