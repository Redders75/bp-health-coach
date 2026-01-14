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
                         sleep_efficiency_pct, vo2_max, stress_score, hrv_mean)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('date'),
                        float(row.get('systolic_mean', 0)) or None,
                        float(row.get('diastolic_mean', 0)) or None,
                        int(row.get('steps', 0)) or None,
                        float(row.get('sleep_hours', 0)) or None,
                        float(row.get('sleep_efficiency_pct', 0)) or None,
                        float(row.get('vo2_max', 0)) or None,
                        float(row.get('stress_score', 0)) or None,
                        float(row.get('hrv_mean', 0)) or None,
                    ))

                    # Add to vector store
                    data = {k: float(v) if v else 0 for k, v in row.items() if k != 'date'}
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
