
# F1 Qualifying Analysis

For my final project I plan to focus on track-based and driver-based qualifying performance, I am currently working on code to obtain the track data.

## Setup

1. Clone repository:
```bash
git clone https://github.com/mvnye/F1-Qualifying-Analysis.git
cd F1-Qualifying-Analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Scripts Overview

So far this project provides two main code files:

### data_collection.py
Downloads and organizes F1 qualifying data into CSV files for each year specified (since 2018). The script allows you to specify several options:
- `--years` (Required): A list of years to fetch data for (e.g., 2021 2022 2023)
- `--cache-dir`: Directory for FastF1's cache (default: f1_cache)
- `--output-dir`: Directory to save fetched data (default: data/original_data)
- `--reload`: Whether to reload existing data (default: False)

Example usage:
```bash
python data_collection.py --years 2020 2021 2022 2023 --cache-dir custom_cache --output-dir custom_output_dir --reload True
```

### dashboard.ipynb
Create final dashboard visualization:


Example data is provided in the data/results_data folder.

## Dashboard 

A final dashboard displaying a timeline of the drivers' careers with average statistics throughout seasons as well as individual qualifying results. 

- position graph throughout season
- comparison to teammates
- their best track
- summarization plot
- improvement/no improvement over time
- possible driver photo 


For more information about project goals, motivations, and background, see `ProjectProposal.pdf`
