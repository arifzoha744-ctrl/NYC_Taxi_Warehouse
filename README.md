====================================================================
               NYC TAXI OPERATIONS DATA WAREHOUSE & ANALYTICS
====================================================================

1. PROJECT OBJECTIVE
--------------------
The goal of this project is to build an end-to-end data engineering 
and business intelligence solution using NYC Yellow Taxi trip records 
from 2024 and 2025. It processes raw data, checks data quality, loads 
clean records into a SQL Data Warehouse, and displays key insights 
in an interactive Power BI dashboard.


2. SOURCE FILES
---------------
- yellow_tripdata_2024-01.parquet
- yellow_tripdata_2024-02.parquet
- yellow_tripdata_2025-01.parquet
- yellow_tripdata_2025-02.parquet
- taxi_zone_lookup.csv (NYC Taxi Zone Lookup table)


3. ARCHITECTURE OVERVIEW
------------------------
Raw Parquet Files ──► Python Validation ──► SQL Staging ──► Data Warehouse ──► Power BI
                               │
                               └──► Quarantine Table (Invalid Records)


4. DATA PROFILING FINDINGS
--------------------------
- Total dataset contains millions of trip records across 4 target months.
- Missing values (nulls) were found in passenger count and congestion fees.
- Minor duplicate records and outlier values (extreme distances/fares) were 
  identified before cleaning.


5. SCHEMA DIFFERENCES (2024 vs 2025)
------------------------------------
- The 2025 dataset introduced a new column: `cbd_congestion_fee`.
- This column was missing in the 2024 source files.
- Strategy: In the warehouse, missing 2024 congestion values are populated 
  with `0` (instead of NULL) to ensure smooth financial additions and avoid 
  reporting errors.


6. DATA QUALITY RULES
---------------------
- Date Check: Pickup time must occur before drop-off time.
- Distance Check: Trip distance must be greater than 0 and under 200 miles.
- Fare Check: Fares and total amounts must not be negative unless flagged as 
  a documented refund/adjustment.
- Location Check: Pickup and Drop-off Zone IDs must exist in the Zone lookup table.


7. QUARANTINE LOGIC
-------------------
- Bad data is NEVER deleted.
- Records failing validation are routed to a `Quarantine` table with a specific 
  `ReasonCode` (e.g., INVALID_DATE, INVALID_DISTANCE, UNKNOWN_ZONE) and `LoadRunID`.


8. DUPLICATE DETECTION LOGIC
----------------------------
- Created a unique deterministic hash key (`RecordHash`) by combining:
  VendorID + PickupDateTime + DropoffDateTime + PULocationID + DOLocationID + FareAmount.
- Any new record matching an existing hash is flagged as a duplicate and quarantined.


9. SQL ARCHITECTURE
-------------------
Built in Microsoft SQL Server using a 3-layer approach:
1. Staging Layer (`stg`): Raw source data ingestion.
2. Warehouse Layer (`dbo`): Star schema model optimized for analytics.
3. ETL Control Layer (`etl`): Logging runs, row counts, and performance status.


10. FACT TABLE GRAIN
--------------------
- Table Name: `FactTaxiTrip`
- Grain: Exactly one row represents one individual taxi trip.


11. DIMENSIONS
--------------
- `DimDate`: Calendar dimension (Year, Quarter, Month, Day, IsWeekend).
- `DimZone`: Taxi location lookup (Borough, Zone, ServiceZone). Used as role-playing 
  dimensions for both Pickup and Drop-off zones.
- `DimPaymentType`: Lookup for cash, credit card, dispute, etc.
- `DimRateCode`: Standard, Airport, Westchester, etc.
- `DimVendor`: Taxi technology vendor provider.


12. INCREMENTAL LOADING
-----------------------
- Loaded dataset month-by-month in 4 separate execution runs.
- Tracked every batch run in `etl.LoadRun` to prevent duplicate re-loading and 
  ensure operational transparency.


13. RECONCILIATION APPROACH
---------------------------
- Formula Verified: Raw Rows = Valid Rows + Quarantined Rows + Duplicate Rows.
- Reconciled both total record counts and financial dollar amounts between raw 
  files and the final warehouse.


14. SQL ANALYSIS
----------------
Executed key SQL analysis answering:
- Busiest hours and peak demand days of the week.
- Top pickup/drop-off routes by volume and total revenue.
- Average fare per mile and tip distributions across payment types.


15. PERFORMANCE OPTIMIZATION
----------------------------
- Measured baseline query performance using `SET STATISTICS IO` and `TIME ON`.
- Created non-clustered indexes on foreign keys (`PickupDateKey`, `PickupZoneKey`, 
  `PaymentTypeKey`).
- Result: Reduced logical reads by over 80% and significantly cut query execution times.


16. POWER BI MODEL
------------------
- Designed a star schema in Power BI.
- Connected directly to SQL Server Data Warehouse.
- Role-playing zone logic handled cleanly to separate Pickup vs Drop-off analytics.


17. DAX MEASURES
----------------
Created key metrics including:
- `Total Trips` = COUNTROWS(FactTaxiTrip)
- `Total Revenue` = SUM(FactTaxiTrip[TotalAmount])
- `Average Fare` = AVERAGE(FactTaxiTrip[FareAmount])
- `Revenue YoY %` = Year-over-Year percentage change in total revenue.


18. DASHBOARD DESIGN
--------------------
- Page 1: Executive Operations (KPI Cards, Monthly Trends, Peak Hours).
- Page 2: Zone & Route Analytics (Top Pickup/Drop-off Zones, Route Ranking, Heatmap).
- Page 3: Fare & Payment Analytics (Payment splits, Tip behavior, Congestion Fees).
- Page 4: Data Quality & ETL Monitoring (Pipeline health, Quarantine reasons, Load history).


19. VALIDATION RESULTS
----------------------
- All Power BI KPIs (Total Trips, Total Revenue, CBD Fees) match 100% against 
  direct SQL validation queries.


20. MAJOR FINDINGS
------------------
- Peak demand occurs on weekday evenings (5 PM - 7 PM).
- Airport routes (JFK / LaGuardia to Midtown) drive the highest revenue per trip.
- Electronic credit card payments capture almost all reported tips (cash tips are 0 in dataset).


21. PROBLEMS FACED
------------------
- Handling schema changes between 2024 and 2025 files (`cbd_congestion_fee`).
- Resolving role-playing zone relationships in Power BI without circular errors.


22. FUTURE IMPROVEMENTS
-----------------------
- Automate pipeline runs using Apache Airflow or Azure Data Factory.
- Set up real-time email alerts for high quarantine failure rates.
====================================================================