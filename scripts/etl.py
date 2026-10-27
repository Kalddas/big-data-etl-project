from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "yellow_tripdata_2025-01.parquet"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"


def extract_data():
    print("Starting extraction...")
    df = pd.read_parquet(DATA_FILE)
    print(f"Original records: {len(df):,}")
    return df


def transform_data(df):
    print("\nStarting transformation...")

    original_count = len(df)

    # Convert pickup and drop-off columns to datetime.
    df["tpep_pickup_datetime"] = pd.to_datetime(
        df["tpep_pickup_datetime"], errors="coerce"
    )
    df["tpep_dropoff_datetime"] = pd.to_datetime(
        df["tpep_dropoff_datetime"], errors="coerce"
    )

    # Count records with invalid dates or impossible trip times.
    invalid_time = (
        df["tpep_pickup_datetime"].isna()
        | df["tpep_dropoff_datetime"].isna()
        | (
            df["tpep_dropoff_datetime"]
            < df["tpep_pickup_datetime"]
        )
    )
    invalid_time_count = int(invalid_time.sum())

    # Exclude records with invalid trip times.
    df = df.loc[~invalid_time].copy()

    # Negative distance is invalid; zero distance is retained for review.
    negative_distance = df["trip_distance"] < 0
    negative_distance_count = int(negative_distance.sum())
    df = df.loc[~negative_distance].copy()

    # Preserve negative fares and totals because they may be adjustments.
    # Preserve missing values where their meaning is unknown.

    # Add useful fields for later analysis.
    df["trip_duration_minutes"] = (
        df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "yellow_tripdata_2025-01-clean.parquet"
    df.to_parquet(output_file, index=False)

    print(f"Original records: {original_count:,}")
    print(f"Excluded invalid-time records: {invalid_time_count:,}")
    print(f"Excluded negative-distance records: {negative_distance_count:,}")
    print(f"Clean records retained: {len(df):,}")
    print(f"Saved cleaned data to: {output_file}")

    return df


def main():
    df = extract_data()
    clean_df = transform_data(df)
    print("\nCleaned data preview:")
    print(clean_df.head())


if __name__ == "__main__":
    main()
