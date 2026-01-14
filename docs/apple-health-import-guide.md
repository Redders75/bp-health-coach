# Apple Health Import Guide

This guide explains how to export your health data from Apple Health and import it into BP Health Coach.

## Overview

The `parse_apple_health.py` script extracts health metrics from your Apple Health export and converts them into a CSV format that BP Health Coach can use.

### Extracted Metrics

| Metric | Description |
|--------|-------------|
| Blood Pressure (Systolic/Diastolic) | Daily averages from all readings |
| Heart Rate | Daily average resting heart rate |
| Steps | Total daily step count |
| Sleep Hours | Total sleep duration |
| VO2 Max | Cardio fitness level |
| HRV (Heart Rate Variability) | Daily average SDNN |
| Respiratory Rate | Breaths per minute |
| Active Calories | Calories burned through activity |
| Exercise Minutes | Apple Watch exercise ring minutes |

## Step 1: Export Your Data from Apple Health

1. Open the **Health** app on your iPhone
2. Tap your **profile picture** in the top-right corner
3. Scroll down and tap **Export All Health Data**
4. Confirm by tapping **Export**
5. Wait for the export to complete (this may take several minutes)
6. Choose how to save/share the file (AirDrop, Files, etc.)

The export creates a file called `export.zip` containing:
- `export.xml` - Your health data (this is what we need)
- `export_cda.xml` - Clinical document format (not used)

## Step 2: Prepare the Export File

1. Unzip `export.zip`
2. Locate `export.xml` inside the unzipped folder
3. Copy `export.xml` to one of these locations:
   - **Default location:** `bp-health-coach/data/raw/export.xml`
   - **Or:** Any location you prefer (specify with `--xml` flag)

```bash
# Example: Copy to default location
mkdir -p data/raw
cp ~/Downloads/apple_health_export/export.xml data/raw/
```

## Step 3: Run the Parser

### Basic Usage (Default Paths)

If your export is at `data/raw/export.xml`:

```bash
python scripts/parse_apple_health.py
```

Output will be saved to `data/raw/health_data.csv`.

### Custom Paths

Specify custom input and output locations:

```bash
python scripts/parse_apple_health.py \
    --xml /path/to/your/export.xml \
    --output /path/to/output.csv
```

### Example Output

```
Parsing Apple Health export: data/raw/export.xml
This may take a few minutes for large files...
  Processed 100,000 records...
  Processed 200,000 records...
Processed 250,000 total records
Found data for 365 days
Writing to data/raw/health_data.csv...
Done! Created data/raw/health_data.csv
```

## Step 4: Import into BP Health Coach

Once you have the CSV file, import it into the database:

```bash
python scripts/import_health_data.py --csv data/raw/health_data.csv
```

## Output CSV Format

The generated CSV contains one row per day with these columns:

| Column | Type | Description |
|--------|------|-------------|
| `date` | YYYY-MM-DD | The date |
| `systolic_mean` | float | Average systolic BP |
| `diastolic_mean` | float | Average diastolic BP |
| `heart_rate_mean` | float | Average heart rate (bpm) |
| `steps` | int | Total steps |
| `sleep_hours` | float | Hours of sleep |
| `sleep_efficiency_pct` | float | Sleep efficiency (not available from Apple Health) |
| `vo2_max` | float | VO2 Max (mL/kg/min) |
| `stress_score` | float | Stress score (not available from Apple Health) |
| `hrv_mean` | float | Average HRV SDNN (ms) |
| `respiratory_rate` | float | Breaths per minute |
| `active_calories` | int | Active calories burned |
| `exercise_minutes` | int | Exercise minutes |

Empty values indicate no data was recorded for that metric on that day.

## Troubleshooting

### "export.xml not found"

Make sure you've:
1. Unzipped the `export.zip` file
2. Placed `export.xml` in the correct location
3. Specified the correct path with `--xml` if not using the default

### Script runs slowly

Apple Health exports can be large (500MB+). The script uses memory-efficient parsing, but large files may still take 5-10 minutes. Progress updates are shown every 100,000 records.

### Missing blood pressure data

Blood pressure readings require:
- A compatible BP monitor connected to Apple Health
- Manual entries in the Health app
- Data synced from another app (e.g., Omron, Withings)

### Missing VO2 Max or HRV

These metrics require:
- **VO2 Max:** Apple Watch with outdoor walks/runs recorded
- **HRV:** Apple Watch worn during sleep or using the Breathe app

## Privacy Notes

- All data processing happens locally on your machine
- The export.xml file contains sensitive health information
- Consider deleting the export.xml after importing
- The CSV file is also sensitive and stored locally in `data/raw/`

## Next Steps

After importing your data, try these commands:

```bash
# Start interactive chat
python -m src.ui.cli chat

# Get today's health briefing
python -m src.ui.cli briefing

# Ask a question about your data
python -m src.ui.cli ask "What was my average BP last week?"
```
