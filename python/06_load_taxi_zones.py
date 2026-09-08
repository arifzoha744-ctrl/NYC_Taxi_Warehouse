from pathlib import Path
import pandas as pd
import pyodbc

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"

file = RAW_DIR / "taxi_zone_lookup.csv"

server = r"."
database = "NYCTaxiWarehouse"

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

df = pd.read_csv(file)

df.columns = df.columns.str.strip()

df = df.rename(columns={
    "service_zone": "ServiceZone"
})

df = df[
    [
        "LocationID",
        "Borough",
        "Zone",
        "ServiceZone"
    ]
]

df["LocationID"] = pd.to_numeric(
    df["LocationID"],
    errors="coerce"
).astype("Int64")

df = df.dropna(subset=["LocationID"])

data = []

for row in df.itertuples(index=False, name=None):
    location_id = int(row[0])
    borough = None if pd.isna(row[1]) else str(row[1])
    zone = None if pd.isna(row[2]) else str(row[2])
    service_zone = None if pd.isna(row[3]) else str(row[3])

    data.append(
        (
            location_id,
            borough,
            zone,
            service_zone
        )
    )

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

cursor.execute("DELETE FROM stg.TaxiZones")
conn.commit()

insert_sql = """
INSERT INTO stg.TaxiZones
(
    LocationID,
    Borough,
    Zone,
    ServiceZone
)
VALUES (?, ?, ?, ?)
"""

cursor.executemany(insert_sql, data)

conn.commit()

cursor.close()
conn.close()

print("Taxi zone rows loaded:", len(data))
print("Taxi zone load completed successfully.")