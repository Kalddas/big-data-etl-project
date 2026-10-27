
import argparse
from getpass import getpass
from pathlib import Path
import logging
import sys

import pandas as pd
from sqlalchemy import URL, create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "yellow_tripdata_2025-01-clean.parquet"
)

TABLE_NAME = "yellow_taxi_trips"
SCHEMA_NAME = "public"
CHUNK_SIZE = 10_000

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def read_dataset() -> pd.DataFrame:
    """Read and validate the existing cleaned dataset."""
    if not DATA_FILE.is_file():
        raise FileNotFoundError(
            f"Cleaned dataset was not found: {DATA_FILE}"
        )

    logger.info("Reading cleaned dataset: %s", DATA_FILE.name)

    try:
        df = pd.read_parquet(DATA_FILE)
    except (OSError, ValueError, ImportError) as exc:
        raise RuntimeError(
            f"Could not read the cleaned Parquet file: {exc}"
        ) from exc

    if df.empty:
        raise ValueError("The cleaned dataset contains no records.")

    required_columns = {
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "trip_distance",
        "trip_duration_minutes",
        "pickup_hour",
    }
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Cleaned dataset is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if df.columns.duplicated().any():
        raise ValueError("The dataset contains duplicate column names.")

    if df["trip_duration_minutes"].isna().any():
        raise ValueError("Trip durations contain missing values.")

    if (df["trip_duration_minutes"] < 0).any():
        raise ValueError("Trip durations contain negative values.")

    if not df["pickup_hour"].between(0, 23).all():
        raise ValueError("Pickup-hour values must be between 0 and 23.")

    logger.info("Dataset validation passed.")
    logger.info("Records ready: %s", f"{len(df):,}")
    return df


def create_database_engine():
    """Prompt for a password without storing it in source code."""
    password = getpass("Enter your PostgreSQL password: ")

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username="postgres",
        password=password,
        host="localhost",
        port=5432,
        database="taxi_etl_db",
    )

    return create_engine(database_url, pool_pre_ping=True)


def validate_destination(engine, df: pd.DataFrame) -> int:
    """Check the destination table and return its current row count."""
    inspector = inspect(engine)

    if not inspector.has_table(TABLE_NAME, schema=SCHEMA_NAME):
        raise RuntimeError(
            f"Destination table {SCHEMA_NAME}.{TABLE_NAME} "
            "does not exist. No data was inserted."
        )

    destination_columns = {
        column["name"]
        for column in inspector.get_columns(
            TABLE_NAME, schema=SCHEMA_NAME
        )
    }

    missing_destination_columns = set(df.columns) - destination_columns
    if missing_destination_columns:
        raise ValueError(
            "Destination table is missing dataset columns: "
            + ", ".join(sorted(missing_destination_columns))
        )

    with engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM public.yellow_taxi_trips")
        ).scalar_one()

    return int(count)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and safely load taxi data into PostgreSQL."
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Explicitly attempt a database load. The table must be empty.",
    )
    args = parser.parse_args()

    engine = None

    try:
        df = read_dataset()
        engine = create_database_engine()

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Database connection successful.")

        current_count = validate_destination(engine, df)
        logger.info("Current destination rows: %s", f"{current_count:,}")

        if not args.load:
            logger.info(
                "VALIDATION ONLY: no records were inserted or modified."
            )
            logger.info(
                "Dataset records: %s. Destination rows: %s.",
                f"{len(df):,}",
                f"{current_count:,}",
            )
            return 0

        if current_count != 0:
            raise RuntimeError(
                "Safety stop: the destination table is not empty. "
                "No data was inserted or deleted."
            )

        logger.info("Starting database load in batches of %s.", CHUNK_SIZE)

        # Keep the load in a single transaction so a failed load can roll back.
        with engine.begin() as connection:
            df.to_sql(
                name=TABLE_NAME,
                con=connection,
                schema=SCHEMA_NAME,
                if_exists="append",
                index=False,
                chunksize=CHUNK_SIZE,
                method=None,
            )

            actual_count = connection.execute(
                text("SELECT COUNT(*) FROM public.yellow_taxi_trips")
            ).scalar_one()

            if actual_count != len(df):
                raise RuntimeError(
                    "Row-count validation failed inside the load transaction."
                )

        logger.info("Load completed. PostgreSQL rows: %s", f"{actual_count:,}")
        return 0

    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        SQLAlchemyError,
        ImportError,
    ) as exc:
        logger.error("%s", exc)
        return 1

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
