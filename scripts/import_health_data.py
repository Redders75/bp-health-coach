#!/usr/bin/env python3
"""
Script to import health data from CSV or existing sources.
"""
import sys
from pathlib import Path
from datetime import date
import csv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database import init_database, get_connection
from src.data.vector_store import get_vector_store
from config.settings import RAW_DATA_DIR


def safe_float(value, default=None):
    """Convert value to float, returning default for empty/invalid values."""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=None):
    """Convert value to int, returning default for empty/invalid values."""
    if value is None or value == '':
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def import_from_csv(csv_path: Path):
    """Import health data from a CSV file."""
    print(f"Importing data from {csv_path}")

    init_database()
    vector_store = get_vector_store()

    imported = 0

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)

        with get_connection() as conn:
            cursor = conn.cursor()

            for row in reader:
                try:
                    # Insert into SQLite
                    cursor.execute("""
                        INSERT OR REPLACE INTO daily_health_data
                        (date, systolic_mean, diastolic_mean, steps, sleep_hours,
                         sleep_efficiency_pct, vo2_max, stress_score, hrv_mean,
                         heart_rate_mean, respiratory_rate, active_calories, exercise_minutes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('date'),
                        safe_float(row.get('systolic_mean')),
                        safe_float(row.get('diastolic_mean')),
                        safe_int(row.get('steps')),
                        safe_float(row.get('sleep_hours')),
                        safe_float(row.get('sleep_efficiency_pct')),
                        safe_float(row.get('vo2_max')),
                        safe_float(row.get('stress_score')),
                        safe_float(row.get('hrv_mean')),
                        safe_float(row.get('heart_rate_mean')),
                        safe_float(row.get('respiratory_rate')),
                        safe_float(row.get('active_calories')),
                        safe_int(row.get('exercise_minutes')),
                    ))

                    # Add to vector store (only if there's meaningful data)
                    data = {}
                    for k, v in row.items():
                        if k != 'date' and v:
                            try:
                                data[k] = float(v)
                            except (ValueError, TypeError):
                                pass

                    if data:  # Only add if we have some data
                        target_date = date.fromisoformat(row['date'])
                        vector_store.add_daily_summary(target_date, data)

                    imported += 1

                except Exception as e:
                    print(f"Error importing row {row.get('date')}: {e}")

            conn.commit()

    print(f"Imported {imported} records.")


def main():
    """Main entry point for data import."""
    import argparse

    parser = argparse.ArgumentParser(description="Import health data")
    parser.add_argument('--csv', type=Path, help="Path to CSV file to import")
    args = parser.parse_args()

    if args.csv:
        if args.csv.exists():
            import_from_csv(args.csv)
        else:
            print(f"File not found: {args.csv}")
            sys.exit(1)
    else:
        print("Please specify a data source with --csv")
        sys.exit(1)


if __name__ == "__main__":
    main()
