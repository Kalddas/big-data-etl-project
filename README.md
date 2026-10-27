# NYC Yellow Taxi ETL and Analysis Project

## Team Information

- **Team Name:** Group 4
- **Course:** Big Data
- **University:** Debre Berhan University

| No. | Team Member | Student ID |
|---:|---|---|
| 1 | Dagmawit Adeferes | DBU 150 1104 |
| 2 | Bruktawit Zelalem | DBU 150 1096 |
| 3 | Bethelehem Beshahe | DBU 150 1061 |
| 4 | Kindie Abera | DBU 150 1310  |
| 5 | Aman Baye | DBU 150 0975 |
| 6 | Amanuel nebey | DBU 150 0983 |

**Before submission:** Confirm the spelling of team members' names and complete the missing student ID digits.

## 1. Project Overview

This project implements an Extract, Transform, and Load (ETL) pipeline using Python, Pandas, and PostgreSQL. It processes NYC Yellow Taxi trip records for January 2025 and analyzes trip demand, fares, distance, duration, and payment types.

## 2. Dataset

- **Source:** NYC Taxi and Limousine Commission (TLC)
- **Dataset:** Yellow Taxi Trip Records, January 2025
- **Download URL:** https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet
- **Original records:** 3,475,226
- **Original columns:** 20
- **Format:** Parquet

## 3. Technologies

- Python
- Pandas
- PyArrow
- SQLAlchemy
- Psycopg
- PostgreSQL 16

## 4. ETL Process

### Extraction

Pandas reads the original Parquet dataset into a DataFrame.

### Transformation

- Pickup and drop-off columns are converted to datetime values.
- Records with missing or invalid trip times, including drop-off times earlier than pickup times, are excluded.
- Records with negative trip distance are excluded.
- Zero-distance trips, negative fares, negative total amounts, and missing values are retained for further review.
- `trip_duration_minutes` is calculated from pickup and drop-off timestamps.
- `pickup_hour` is derived from the pickup timestamp.
- The cleaned dataset is saved as a Parquet file.

### Loading

The cleaned data is stored in the PostgreSQL database `taxi_etl_db`, in the table `public.yellow_taxi_trips`.

The loader checks whether the destination table exists and whether it already contains records. It stops if the table is populated, helping prevent accidental duplicate loading. It uses append mode rather than replacing the table.

## 5. ETL Validation

- Original records: 3,475,226
- Invalid-time records excluded: 124
- Negative-distance records excluded: 0
- Cleaned records: 3,475,102
- Records loaded into PostgreSQL: 3,475,102
- The cleaned dataset and database table row counts match.
- All 3,475,102 rows have non-null, unique `trip_id` values.
- The loader's safety check stops loading when the destination table already contains data.

## 6. Database Schema

The `public.yellow_taxi_trips` table has 23 columns: the original 20 dataset fields, two derived fields (`trip_duration_minutes` and `pickup_hour`), and the generated `trip_id` primary key.

The `trip_id` column is a database-generated `BIGINT` identity column used to uniquely identify each stored row. It is a technical row identifier, not an original TLC trip identifier.

The `sql/schema.sql` file contains the table definition, identity column, and primary-key constraint.

## 7. SQL Analysis Results

- Total trips analyzed: 3,475,102
- Busiest pickup hour: 18:00 (6 PM), with 267,949 trips
- Second busiest pickup hour: 17:00 (5 PM), with 253,511 trips
- Average fare amount: USD 17.08
- Average total amount: USD 25.61
- Sum of recorded total amounts: USD 89,001,917.17
- Average trip distance: 5.86 miles
- Average trip duration among non-negative durations: 15.03 minutes
- Most frequent payment code: 1, with 2,444,387 trips

Amounts are reported in USD as represented by the dataset. The sum of `total_amount` is a recorded trip-amount total and should not be interpreted as verified net business revenue. Payment codes require reference documentation before assigning meanings.

The SQL queries are saved in `sql/analysis.sql`.

## 8. Data Quality Observations

The database quality checks found:

- Missing pickup timestamps: 0
- Missing drop-off timestamps: 0
- Negative trip durations: 0
- Zero-duration trips: 1,927
- Zero-distance trips: 90,893
- Negative trip distances: 0
- Missing fare amounts: 0
- Missing total amounts: 0
- Missing payment types: 0
- Rows with payment code 0: 540,031

Zero-duration and zero-distance trips and payment code 0 were retained for further review rather than automatically classified as invalid.

## 9. How to Run the Project

Run these commands from the project directory in PowerShell.

### Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

### Run extraction and transformation

```powershell
.\.venv\Scripts\python.exe .\scripts\etl.py
```

### Prepare the database schema

Create the `taxi_etl_db` database if it does not already exist, then run `sql/schema.sql` against that database before loading data.

**Important:** The schema script creates the table. Use it on a fresh database where `public.yellow_taxi_trips` does not already exist. Do not run it against the existing populated table.

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d taxi_etl_db -v ON_ERROR_STOP=1 -f ".\sql\schema.sql"
```

### Load the cleaned data

Run this only when the destination table exists and is empty:

```powershell
.\.venv\Scripts\python.exe .\scripts\load.py
```

Enter the PostgreSQL password when prompted. The loader stops if the destination table already contains records.

### Run the SQL analysis

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d taxi_etl_db -P pager=off -v ON_ERROR_STOP=1 -f ".\sql\analysis.sql"
```

## 10. Conclusion

The ETL pipeline successfully extracted, transformed, and loaded more than 3.4 million taxi trip records. Row-count and primary-key validation confirmed that the cleaned dataset and PostgreSQL table contain the expected records. SQL analysis summarized pickup-hour demand, fares, trip distance, duration, and payment-code distributions.

## 11. Possible Improvements

- Add automated data-quality tests.
- Review missing values and unusual fare or distance records.
- Add suitable indexes for frequently queried columns.
- Define additional data-quality constraints where appropriate.
- Create charts or a dashboard to present the analysis results.
