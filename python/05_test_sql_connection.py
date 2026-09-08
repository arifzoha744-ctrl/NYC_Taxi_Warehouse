import pyodbc

server = r"."
database = "NYCTaxiWarehouse"

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(connection_string, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT DB_NAME()")
    result = cursor.fetchone()

    print("SQL connection successful")
    print("Database:", result[0])

    conn.close()

except Exception as e:
    print("SQL connection failed")
    print(e)