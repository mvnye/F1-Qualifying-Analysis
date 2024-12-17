# F1 Qualifying Analysis
For my final project I plan to focus on track-based and driver-based qualifying performance, I am currently working on code to obtain the track data.

## Setup
1. Clone repository:
```bash
git clone https://github.com/mvnye/F1-Qualifying-Analysis.git
cd F1-Qualifying-Analysis
```

2. Install pipenv if not already installed:
```bash
pip install pipenv
```

3. Set up the virtual environment and install dependencies:
```bash
pipenv shell
pipenv install
```

4. Run the data pipeline:
```bash
python data_collection.py --years 2023 2024 --output-dir data
python data_processing.py --input-dir data --output-dir data
python dashboard.py
```

Note: The scripts will automatically create necessary directories.

## Scripts Overview
The project consists of three main Python scripts:

### data_collection.py
Downloads and organizes F1 qualifying data into CSV files for each year specified. Options:
- `--years` (Required): List of years to fetch data for (e.g., 2021 2022 2023)
- `--cache-dir`: Directory for FastF1's cache (default: f1_cache)
- `--output-dir`: Directory to save fetched data (default: data)
- `--reload`: Whether to reload existing data (default: False)

Example usage:
```bash
python data_collection.py --years 2020 2021 2022 2023
```

### data_processing.py
Processes the raw qualifying data and creates the career timeline dataset. Options:
- `--input-dir`: Directory containing the raw CSV files (default: data)
- `--output-dir`: Directory for processed output (default: data)
- `--filename`: Name for the output file (default: career_timeline.json)

Features:
- Combines qualifying data from multiple years
- Calculates gaps to pole position
- Computes teammate comparisons
- Generates season statistics

### dashboard.py
Creates an interactive dashboard visualization that displays:
- Position graphs throughout each season
- Teammate comparisons
- Best qualifying performances
- Average statistics per season
- Detailed race-by-race analysis
- Performance trends over time

The dashboard includes:
- Driver selection dropdown
- Year-by-year timeline
- Interactive qualifying position charts
- Detailed event statistics
- Gap to pole position analysis
- Teammate comparison metrics

## Data Structure
- Raw data is stored in CSV files in the data directory
- Processed data is saved as career_timeline.json
- FastF1 cache is stored in f1_cache directory

## Dashboard Features
The final dashboard provides:
- Comprehensive timeline of drivers' careers
- Position tracking throughout seasons
- Gap to pole position analysis
- Teammate comparison metrics
- Best qualifying achievements
- Season summarization statistics
- Performance trend analysis

For more information about project goals, motivations, and background, see `ProjectProposal.pdf`
