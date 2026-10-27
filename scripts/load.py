from getpass import getpass
from pathlib import Path

import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "yellow_tripdata_2025-01-clean.parquet"
)

TABLE_NAME = "yellow_taxi_trips"


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Cleaned dataset not found: {DATA_FILE}")

    print("Reading cleaned dataset...")
    df = pd.read_parquet(DATA_FILE)
    expected_count = len(df)
    print(f"Records in cleaned dataset: {expected_count:,}")

    password = getpass("Enter your PostgreSQL password: ")

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username="postgres",
        password=password,
        host="localhost",
        port=5432,
        database="taxi_etl_db",
    )

    engine = create_engine(database_url)

    try:
        print("\nConnecting to PostgreSQL...")

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection successful.")

        with engine.connect() as connection:
            table_exists = connection.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = :table_name
                    )
                    """
                ),
                {"table_name": TABLE_NAME},
            ).scalar_one()

            if not table_exists:
                raise RuntimeError(
                    "Destination table does not exist. "
                    "Create and validate the table schema first."
                )

            current_count = connection.execute(
                text("SELECT COUNT(*) FROM public.yellow_taxi_trips")
            ).scalar_one()

        if current_count > 0:
            raise RuntimeError(
                f"Safety stop: destination table already contains "
                f"{current_count:,} rows. No data was inserted."
            )

        print(f"\nLoading data into {TABLE_NAME}...")

        df.to_sql(
            name=TABLE_NAME,
            con=engine,
            schema="public",
            if_exists="append",
            index=False,
            chunksize=10000,
            method=None,
        )

        with engine.connect() as connection:
            actual_count = connection.execute(
                text("SELECT COUNT(*) FROM public.yellow_taxi_trips")
            ).scalar_one()

        print("\nLOAD COMPLETED!")
        print(f"Rows in PostgreSQL: {actual_count:,}")
        print(f"Rows in cleaned dataset: {expected_count:,}")
        print(f"Row counts match: {actual_count == expected_count}")

        if actual_count != expected_count:
            raise RuntimeError("Validation failed: row counts do not match.")

    except SQLAlchemyError as error:
        print(f"\nDatabase error: {error}")
        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()