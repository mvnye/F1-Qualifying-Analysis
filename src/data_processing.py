from pathlib import Path
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def process_qualifying_data(quali_data: pd.DataFrame) -> list:
    """
    Process qualifying data to create a timeline of driver performances.
    
    Args:
        quali_data: DataFrame containing qualifying session data
        
    Returns:
        List of dictionaries containing processed data for each driver's season
        
    Raises:
        ValueError: If required columns are missing from the input DataFrame
    """
    logger.info("Processing qualifying data...")
    timeline_data: list = []
    
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
        
        for event_name, event_data in year_data.groupby('EventName'):
            pole_data = event_data[event_data['Position'] == 1].iloc[0]
            pole_time = pole_data['Q3Seconds']
            
            for team, team_data in event_data.groupby('TeamName'):
                gaps = calculate_teammate_gaps(team_data)
                
                for driver in team_data['BroadcastName'].unique():
                    driver_data = team_data[team_data['BroadcastName'] == driver].iloc[0]
                    best_time = get_best_time(driver_data)
                    qualifying_position = driver_data['Position'] if pd.notna(driver_data['Position']) else np.nan
                    
                    gap_to_pole = calculate_gap_to_pole(qualifying_position, best_time, pole_time)
                    event_summary = create_event_summary(event_name, qualifying_position, gap_to_pole, gaps[driver])
                    
                    # Find or create driver entry
                    driver_entry = next(
                        (item for item in timeline_data if item['year'] == year and item['driver'] == driver),
                        None
                    )
                    
                    if driver_entry is None:
                        driver_entry = create_driver_entry(year, driver, team)
                        timeline_data.append(driver_entry)
                    
                    # Update driver entry
                    driver_entry['events'].append(event_summary)
                    driver_entry['positions'].append(qualifying_position)
                    driver_entry['totalEvents'] += 1
                    
                    if not pd.isna(gap_to_pole):
                        driver_entry['gapToPole_values'].append(gap_to_pole)
                    if not pd.isna(gaps[driver]):
                        driver_entry['teammateGap_values'].append(gaps[driver])
                        driver_entry['completeDataCount'] += 1
    
    # Calculate final statistics
    for entry in timeline_data:
        valid_positions = [pos for pos in entry['positions'] if not pd.isna(pos)]
        valid_gaps_to_pole = [gap for gap in entry['gapToPole_values'] if not pd.isna(gap)]
        valid_teammate_gaps = [gap for gap in entry['teammateGap_values'] if not pd.isna(gap)]
        
        entry['avgQualifyingPosition'] = np.mean(valid_positions) if valid_positions else np.nan
        entry['avgGapToPole'] = np.mean(valid_gaps_to_pole) if valid_gaps_to_pole else np.nan
        entry['avgTeammateGap'] = np.mean(valid_teammate_gaps) if valid_teammate_gaps else np.nan
        entry['dataCompleteness'] = entry['completeDataCount'] / entry['totalEvents'] if entry['totalEvents'] > 0 else 0
        
        # Clean up 
        for key in ['positions', 'gapToPole_values', 'teammateGap_values', 
                   'completeDataCount', 'totalEvents']:
            del entry[key]
    
    return timeline_data

if __name__ == "__main__":
    logger.info("Starting data processing ")
    quali_data = combine_csv_files('data/results_data')
    if quali_data is not None:
        quali_data = convert_time(quali_data)
        career_timeline_data = process_qualifying_data(quali_data)
        logger.info("Processing completed")
    else:
        logger.error("Failed to load qualifying data")