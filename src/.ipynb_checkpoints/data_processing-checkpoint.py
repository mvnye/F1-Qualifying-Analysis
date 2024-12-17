from pathlib import Path
import pandas as pd
import numpy as np
import logging
import argparse 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
#current 
def combine_csv_files(folder_path: str | Path) -> pd.DataFrame | None:
    """
    Read all CSV files from a folder and combine them into a single DataFrame.
    
    Parameters:
    folder_path (str): Path to the folder containing CSV files
    
    Returns:
    pandas.DataFrame: Combined DataFrame from all CSV files

    Raises:
        FileNotFoundError: If the folder path doesn't exist
    
    """
    path = Path(folder_path)
    all_dfs = []
    
    # Loop through all files in the folder
    for file in path.glob('*.csv'):
        try:
            df = pd.read_csv(file)
            # Append to the list
            all_dfs.append(df)
            
            print(f"Successfully read: {file.name}")
            
        except Exception as e:
            print(f"Error reading {file.name}: {str(e)}")
    
    # Combine all DataFrames
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        print(f"\nTotal number of files combined: {len(all_dfs)}")
        print(f"Total rows in DataFrame: {len(combined_df)}")
        return combined_df
    else:
        print("No CSV files found in the specified folder!")
        return None
    

def convert_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert time columns to timedelta and seconds.
    
    Args:
        df: DataFrame containing qualifying time data
        
    Returns:
        DataFrame with added columns for qualifying times in seconds
    """
    df['Q1'] = pd.to_timedelta(df['Q1'])
    df['Q2'] = pd.to_timedelta(df['Q2'])
    df['Q3'] = pd.to_timedelta(df['Q3'])

    df['Q1Seconds'] = df['Q1'].apply(lambda x: x.total_seconds())
    df['Q2Seconds'] = df['Q2'].apply(lambda x: x.total_seconds())
    df['Q3Seconds'] = df['Q3'].apply(lambda x: x.total_seconds())   
    
    return df 

def get_best_time(driver_data: pd.Series) -> float | None:
    """Get best qualifying time from Q1, Q2, or Q3."""
    if pd.notna(driver_data['Q3Seconds']):
        return driver_data['Q3Seconds']
    elif pd.notna(driver_data['Q2Seconds']):
        return driver_data['Q2Seconds']
    elif pd.notna(driver_data['Q1Seconds']):
        return driver_data['Q1Seconds']
    return None

def calculate_gap_to_pole(position: float, best_time: float | None, pole_time: float) -> float:
    """Calculate gap to pole position."""
    if pd.isna(position):
        return np.nan
    elif position == 1:
        return 0.0
    elif best_time is None or pd.isna(pole_time):
        return np.nan
    return best_time - pole_time

def create_event_summary(event_name: str, position: float, gap_to_pole: float, teammate_gap: float) -> dict:
    """Create event summary dictionary."""
    return {
        'round': event_name,
        'position': position,
        'gapToPole': gap_to_pole,
        'teammateGap': teammate_gap,
        'hasTeammateData': not pd.isna(teammate_gap)
    }

def create_driver_entry(year: int, driver: str, team: str) -> dict:
    """Create initial driver entry dictionary."""
    return {
        'year': year,
        'driver': driver,
        'team': team,
        'events': [],
        'positions': [],
        'gapToPole_values': [],
        'teammateGap_values': [],
        'completeDataCount': 0,
        'totalEvents': 0
    }

def calculate_teammate_gaps(team_data: pd.DataFrame) -> dict:
    """Calculate gaps between teammates."""
    drivers = team_data['BroadcastName'].unique()
    gaps: dict = {driver: np.nan for driver in drivers}
    
    if len(drivers) == 2:
        driver1, driver2 = drivers
        time1_data = team_data[team_data['BroadcastName'] == driver1].iloc[0]
        time2_data = team_data[team_data['BroadcastName'] == driver2].iloc[0]
        
        time1 = get_best_time(time1_data)
        time2 = get_best_time(time2_data)

        if time1 is not None and time2 is not None:
            gaps.update({
                driver1: time1 - time2,
                driver2: time2 - time1
            })
    
    return gaps

def create_driver_entry(year: int, driver: str, team: str) -> dict:
    """Create initial driver entry dictionary."""
    return {
        'year': year,
        'driver': driver,
        'teams': [{
            'team': team,
            'events': [],
            'positions': [],
            'gapToPole_values': [],
            'teammateGap_values': [],
            'completeDataCount': 0,
            'totalEvents': 0
        }]
    }



def process_qualifying_data(quali_data: pd.DataFrame) -> list:
    """
    Process qualifying data to create a timeline of driver performances.
    """
    logger.info("Processing qualifying data...")
    timeline_data: list = []
    yearly_event_order = {}

    required_columns = [
        'DriverNumber', 'BroadcastName', 'TeamName', 'Position', 
        'Q1', 'Q2', 'Q3', 'Year', 'EventName', 'WetSession', 
        'Q1Seconds', 'Q2Seconds', 'Q3Seconds'
    ]
    
    missing_columns = [col for col in required_columns if col not in quali_data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    for year in quali_data['Year'].unique():
        logger.info(f"Processing year: {year}")
        year_data = quali_data[quali_data['Year'] == year]
        all_events = list(year_data['EventName'].unique())
        yearly_event_order[year] = all_events
        
        
        for driver in year_data['BroadcastName'].unique():
            # Get all events for this driver across any teams
            driver_year_data = year_data[year_data['BroadcastName'] == driver]
            
            # Get initial team
            current_team = driver_year_data.iloc[0]['TeamName']
            driver_entry = create_driver_entry(year, driver, current_team)
            current_team_data = driver_entry['teams'][0]
            
            # Process each event
            for event_name in all_events:
                event_data = year_data[year_data['EventName'] == event_name]
                
                if event_data.empty:
                    continue
                
                # Get pole time for the event
                pole_data = event_data[event_data['Position'] == 1]
                pole_time = pole_data.iloc[0]['Q3Seconds'] if not pole_data.empty else np.nan
                
                # Get driver's data for this event
                driver_event_data = event_data[event_data['BroadcastName'] == driver]
                
                if not driver_event_data.empty:
                    # Driver participated - get their data
                    this_event_data = driver_event_data.iloc[0]
                    event_team = this_event_data['TeamName']
                    
                    # Check if driver changed teams
                    if event_team != current_team:
                        # Create new team entry
                        current_team = event_team
                        current_team_data = {
                            'team': current_team,
                            'events': [],
                            'positions': [],
                            'gapToPole_values': [],
                            'teammateGap_values': [],
                            'completeDataCount': 0,
                            'totalEvents': 0
                        }
                        driver_entry['teams'].append(current_team_data)
                    
                    # Get teammate gaps for this specific team and event
                    team_event_data = event_data[event_data['TeamName'] == current_team]
                    gaps = calculate_teammate_gaps(team_event_data)
                    
                    best_time = get_best_time(this_event_data)
                    qualifying_position = this_event_data['Position'] if pd.notna(this_event_data['Position']) else np.nan
                    gap_to_pole = calculate_gap_to_pole(qualifying_position, best_time, pole_time)
                else:
                    # Driver didn't participate in this event
                    qualifying_position = np.nan
                    gap_to_pole = np.nan
                    gaps = {driver: np.nan}
                
                event_summary = create_event_summary(
                    event_name,
                    qualifying_position,
                    gap_to_pole,
                    gaps.get(driver, np.nan)
                )
                
                current_team_data['events'].append(event_summary)
                
                # Update statistics tracking
                if not pd.isna(qualifying_position):
                    current_team_data['positions'].append(qualifying_position)
                if not pd.isna(gap_to_pole):
                    current_team_data['gapToPole_values'].append(gap_to_pole)
                if not pd.isna(gaps.get(driver, np.nan)):
                    current_team_data['teammateGap_values'].append(gaps.get(driver, np.nan))
                    current_team_data['completeDataCount'] += 1
                current_team_data['totalEvents'] += 1
            
            # Calculate statistics for each team
            for team_data in driver_entry['teams']:
                valid_positions = [pos for pos in team_data['positions'] if not pd.isna(pos)]
                valid_gaps_to_pole = [gap for gap in team_data['gapToPole_values'] if not pd.isna(gap)]
                valid_teammate_gaps = [gap for gap in team_data['teammateGap_values'] if not pd.isna(gap)]
                
                team_data['avgQualifyingPosition'] = np.mean(valid_positions) if valid_positions else np.nan
                team_data['avgGapToPole'] = np.mean(valid_gaps_to_pole) if valid_gaps_to_pole else np.nan
                team_data['avgTeammateGap'] = np.mean(valid_teammate_gaps) if valid_teammate_gaps else np.nan
                team_data['dataCompleteness'] = team_data['completeDataCount'] / team_data['totalEvents'] if team_data['totalEvents'] > 0 else 0
                
                # Clean up 
                for key in ['positions', 'gapToPole_values', 'teammateGap_values', 
                           'completeDataCount', 'totalEvents']:
                    del team_data[key]
            
            # After processing all events for this driver, append their entry
            timeline_data.append(driver_entry)
    
    return timeline_data, yearly_event_order

def generate_dashboard_data(data_folder: str | Path, output_file: str | Path) -> None:
    """
    Generate and save dashboard data by running previous functions.

    Args:
        data_folder: Path to the folder containing raw CSV files.
        output_file: Path where the processed data will be saved as a JSON file.
    """
    logger.info("Generating dashboard data...")
    # Combine all CSVs into one DataFrame
    quali_data = combine_csv_files(data_folder)
    
    if quali_data is None:
        logger.error("No data processed: Failed to combine CSV files.")
        return
    
    # Convert times to seconds
    quali_data = convert_time(quali_data)
    
    # Process data into career timeline format
    career_timeline_data, yearly_event_order = process_qualifying_data(quali_data)
    
    # Save processed data to JSON files
    output_base_path = Path(output_file)
    output_base_path.parent.mkdir(parents=True, exist_ok=True)

    # Save main timeline data
    timeline_path = output_base_path / 'career_timeline_data.json'
    pd.DataFrame(career_timeline_data).to_json(timeline_path, orient='records', indent=4)

    #   Save event order data
    race_order_path = output_base_path / 'race_order.json'
    pd.Series(yearly_event_order).to_json(race_order_path, indent=4)

def main() -> None:
    """Main function to process F1 qualifying data and generate dashboard."""
    parser = argparse.ArgumentParser(description='Process F1 Qualifying Data')
    parser.add_argument('--input-dir', default='../data', help='Directory for input files')
    parser.add_argument('--output-dir', default='../data', help='Directory for output files')
    
    args = parser.parse_args()
    
    # Call function to generate dashboard data
    generate_dashboard_data(args.input_dir, args.output_dir)
    
    print(f"Dashboard data successfully generated and saved to:")
    print(f"  {args.output_dir}/career_timeline_data.json")
    print(f"  {args.output_dir}/race_order.json")

if __name__ == "__main__":
    main()