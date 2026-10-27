
from pathlib import Path
import logging
import sys

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "yellow_tripdata_2025-01.parquet"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "yellow_tripdata_2025-01-clean-validated.parquet"

REQUIRED_COLUMNS = {
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "trip_distance",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def extract_data() -> pd.DataFrame:
    """Read the source dataset and validate its required columns."""
    if not DATA_FILE.is_file():
        raise FileNotFoundError(
            f"Source dataset was not found: {DATA_FILE}"
        )

    logger.info("Reading source dataset: %s", DATA_FILE.name)

    try:
        df = pd.read_parquet(DATA_FILE)
    except (OSError, ValueError, ImportError) as exc:
        raise RuntimeError(
            f"Could not read the source Parquet file: {exc}"
        ) from exc

    if df.empty:
        raise ValueError("The source dataset contains no records.")

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(
            "Source dataset is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    logger.info("Source records: %s", f"{len(df):,}")
    logger.info("Source columns: %s", len(df.columns))
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean invalid trip times and distances and add analysis columns."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input data must be a Pandas DataFrame.")

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(
            "Input data is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    original_count = len(df)
    if original_count == 0:
        raise ValueError("Cannot transform an empty dataset.")

    logger.info("Starting data transformation.")

    # Work on a copy; do not mutate the caller's DataFrame.
    df = df.copy()

    df["tpep_pickup_datetime"] = pd.to_datetime(
        df["tpep_pickup_datetime"], errors="coerce"
    )
    df["tpep_dropoff_datetime"] = pd.to_datetime(
        df["tpep_dropoff_datetime"], errors="coerce"
    )
    df["trip_distance"] = pd.to_numeric(
        df["trip_distance"], errors="coerce"
    )

    invalid_time = (
        df["tpep_pickup_datetime"].isna()
        | df["tpep_dropoff_datetime"].isna()
        | (
            df["tpep_dropoff_datetime"]
            < df["tpep_pickup_datetime"]
        )
    )
    invalid_time_count = int(invalid_time.sum())
    df = df.loc[~invalid_time].copy()

    negative_distance = df["trip_distance"] < 0
    negative_distance_count = int(negative_distance.sum())
    df = df.loc[~negative_distance].copy()

    if df.empty:
        raise ValueError(
            "No records remain after cleaning. "
            "The output file was not written."
        )

    # Preserve zero-distance trips, negative fares/totals, and unknown values.
    df["trip_duration_minutes"] = (
        df["tpep_dropoff_datetime"]
        - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour

    if df["trip_duration_minutes"].isna().any():
        raise ValueError("Unexpected missing trip durations after cleaning.")

    if (df["trip_duration_minutes"] < 0).any():
        raise ValueError("Negative trip durations remain after cleaning.")

    if not df["pickup_hour"].between(0, 23).all():
        raise ValueError("Pickup hour validation failed.")

    logger.info("Original records: %s", f"{original_count:,}")
    logger.info("Invalid-time records excluded: %s", f"{invalid_time_count:,}")
    logger.info(
        "Negative-distance records excluded: %s",
        f"{negative_distance_count:,}",
    )
    logger.info("Clean records retained: %s", f"{len(df):,}")

    return df


def save_data(df: pd.DataFrame) -> None:
    """Save to a new output path without overwriting an existing file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing output: {OUTPUT_FILE}\n"
            "Choose a new output filename before running again."
        )

    temporary_file = OUTPUT_FILE.with_suffix(".tmp.parquet")

    if temporary_file.exists():
        raise FileExistsError(
            f"Temporary file already exists: {temporary_file}. "
            "Inspect it before continuing."
        )

    try:
        df.to_parquet(temporary_file, index=False)

        # Verify that the new file can be read and has the expected row count.
        check_df = pd.read_parquet(temporary_file)
        if len(check_df) != len(df):
            raise RuntimeError(
                "Saved file row count does not match the transformed data."
            )

        if list(check_df.columns) != list(df.columns):
            raise RuntimeError(
                "Saved file columns do not match the transformed data."
            )

        # Refuse to replace any output that appeared while processing.
        if OUTPUT_FILE.exists():
            raise FileExistsError(
                f"Output appeared during processing: {OUTPUT_FILE}"
            )

        temporary_file.rename(OUTPUT_FILE)

    except Exception:
        # Remove only the temporary file created by this run.
        if temporary_file.exists():
            temporary_file.unlink()
        raise

    logger.info("Validated output saved to: %s", OUTPUT_FILE)
    logger.info("Verified output records: %s", f"{len(df):,}")


def main() -> int:
    try:
        source_df = extract_data()
        clean_df = transform_data(source_df)
        save_data(clean_df)

        logger.info("ETL transformation completed successfully.")
        logger.info("The original cleaned dataset was not modified.")
        return 0

    except (OSError, ValueError, TypeError, RuntimeError, ImportError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
