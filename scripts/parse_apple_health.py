#!/usr/bin/env python3
"""
Parse Apple Health export.xml and extract relevant health data.
"""
import sys
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict
import xml.etree.ElementTree as ET
import csv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def parse_apple_health_export(xml_path: Path, output_csv: Path):
    """Parse Apple Health export and create CSV for import."""
    print(f"Parsing Apple Health export: {xml_path}")
    print("This may take a few minutes for large files...")

    # Data collectors - keyed by date
    daily_data = defaultdict(lambda: {
        'systolic_readings': [],
        'diastolic_readings': [],
        'heart_rate_readings': [],
        'steps': 0,
        'sleep_hours': 0,
        'sleep_analysis': [],
        'vo2_max': None,
        'hrv_readings': [],
        'respiratory_rate': [],
        'active_calories': 0,
        'exercise_minutes': 0,
    })

    # Type mappings for Apple Health
    type_map = {
        'HKQuantityTypeIdentifierBloodPressureSystolic': 'systolic',
        'HKQuantityTypeIdentifierBloodPressureDiastolic': 'diastolic',
        'HKQuantityTypeIdentifierHeartRate': 'heart_rate',
        'HKQuantityTypeIdentifierStepCount': 'steps',
        'HKQuantityTypeIdentifierVO2Max': 'vo2_max',
        'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'hrv',
        'HKQuantityTypeIdentifierRespiratoryRate': 'respiratory_rate',
        'HKQuantityTypeIdentifierActiveEnergyBurned': 'active_calories',
        'HKQuantityTypeIdentifierAppleExerciseTime': 'exercise_minutes',
    }

    record_count = 0

    # Use iterparse for memory efficiency with large files
    context = ET.iterparse(xml_path, events=('end',))

    for event, elem in context:
        if elem.tag == 'Record':
            record_type = elem.get('type', '')

            if record_type in type_map:
                try:
                    # Parse date
                    start_date_str = elem.get('startDate', '')
                    if start_date_str:
                        dt = datetime.strptime(start_date_str[:10], '%Y-%m-%d')
                        day_key = dt.date().isoformat()

                        value = float(elem.get('value', 0))
                        data_type = type_map[record_type]

                        if data_type == 'systolic':
                            daily_data[day_key]['systolic_readings'].append(value)
                        elif data_type == 'diastolic':
                            daily_data[day_key]['diastolic_readings'].append(value)
                        elif data_type == 'heart_rate':
                            daily_data[day_key]['heart_rate_readings'].append(value)
                        elif data_type == 'steps':
                            daily_data[day_key]['steps'] += int(value)
                        elif data_type == 'vo2_max':
                            daily_data[day_key]['vo2_max'] = value
                        elif data_type == 'hrv':
                            daily_data[day_key]['hrv_readings'].append(value)
                        elif data_type == 'respiratory_rate':
                            daily_data[day_key]['respiratory_rate'].append(value)
                        elif data_type == 'active_calories':
                            daily_data[day_key]['active_calories'] += value
                        elif data_type == 'exercise_minutes':
                            daily_data[day_key]['exercise_minutes'] += int(value)

                        record_count += 1
                        if record_count % 100000 == 0:
                            print(f"  Processed {record_count:,} records...")

                except (ValueError, TypeError):
                    pass

            # Clear element to save memory
            elem.clear()

        elif elem.tag == 'SleepAnalysis' or (elem.tag == 'Record' and 'Sleep' in elem.get('type', '')):
            try:
                start_str = elem.get('startDate', '')
                end_str = elem.get('endDate', '')
                if start_str and end_str:
                    start_dt = datetime.strptime(start_str[:19], '%Y-%m-%d %H:%M:%S')
                    end_dt = datetime.strptime(end_str[:19], '%Y-%m-%d %H:%M:%S')
                    duration_hours = (end_dt - start_dt).total_seconds() / 3600
                    day_key = start_dt.date().isoformat()
                    daily_data[day_key]['sleep_hours'] += duration_hours
            except (ValueError, TypeError):
                pass
            elem.clear()

    print(f"Processed {record_count:,} total records")
    print(f"Found data for {len(daily_data)} days")

    # Write to CSV
    print(f"Writing to {output_csv}...")

    with open(output_csv, 'w', newline='') as f:
        fieldnames = [
            'date', 'systolic_mean', 'diastolic_mean', 'heart_rate_mean',
            'steps', 'sleep_hours', 'sleep_efficiency_pct', 'vo2_max',
            'stress_score', 'hrv_mean', 'respiratory_rate', 'active_calories',
            'exercise_minutes'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for day_key in sorted(daily_data.keys()):
            data = daily_data[day_key]

            # Calculate means
            systolic_mean = sum(data['systolic_readings']) / len(data['systolic_readings']) if data['systolic_readings'] else None
            diastolic_mean = sum(data['diastolic_readings']) / len(data['diastolic_readings']) if data['diastolic_readings'] else None
            hr_mean = sum(data['heart_rate_readings']) / len(data['heart_rate_readings']) if data['heart_rate_readings'] else None
            hrv_mean = sum(data['hrv_readings']) / len(data['hrv_readings']) if data['hrv_readings'] else None
            resp_rate = sum(data['respiratory_rate']) / len(data['respiratory_rate']) if data['respiratory_rate'] else None

            row = {
                'date': day_key,
                'systolic_mean': round(systolic_mean, 1) if systolic_mean else '',
                'diastolic_mean': round(diastolic_mean, 1) if diastolic_mean else '',
                'heart_rate_mean': round(hr_mean, 1) if hr_mean else '',
                'steps': data['steps'] if data['steps'] > 0 else '',
                'sleep_hours': round(data['sleep_hours'], 2) if data['sleep_hours'] > 0 else '',
                'sleep_efficiency_pct': '',  # Not directly available from Apple Health
                'vo2_max': data['vo2_max'] if data['vo2_max'] else '',
                'stress_score': '',  # Would need to calculate from HRV
                'hrv_mean': round(hrv_mean, 1) if hrv_mean else '',
                'respiratory_rate': round(resp_rate, 1) if resp_rate else '',
                'active_calories': round(data['active_calories'], 0) if data['active_calories'] > 0 else '',
                'exercise_minutes': data['exercise_minutes'] if data['exercise_minutes'] > 0 else '',
            }
            writer.writerow(row)

    print(f"Done! Created {output_csv}")
    return output_csv


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Parse Apple Health export")
    parser.add_argument('--xml', type=Path, default=project_root / 'data' / 'raw' / 'export.xml',
                        help="Path to Apple Health export.xml")
    parser.add_argument('--output', type=Path, default=project_root / 'data' / 'raw' / 'health_data.csv',
                        help="Output CSV path")
    args = parser.parse_args()

    if not args.xml.exists():
        print(f"Error: {args.xml} not found")
        sys.exit(1)

    parse_apple_health_export(args.xml, args.output)


if __name__ == "__main__":
    main()
