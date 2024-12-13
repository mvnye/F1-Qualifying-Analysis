import fastf1
import pandas as pd
import logging
import time
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import argparse
import gc
import sys

class F1DataFetcher:
    def __init__(self, cache_dir='f1_cache', output_dir='f1_data', reload=False):
        """
        Initialize F1 data fetcher.
        
        Args:
            cache_dir (str): Directory for FastF1 cache
            output_dir (str): Directory for output CSV files
            reload (bool): If True, reload data 
        """
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.reload = reload
        
        # Create directories with parent directories if needed
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        
        # Setup logging
        self._setup_logging()
        
        # Initialize FastF1
        self._setup_fastf1()
        
    def _setup_logging(self):
        """Configure logging for errors."""
        log_file = self.output_dir / 'data_collection.log'
    
        logging.basicConfig(
            level=logging.WARNING,  # show warnings and errors 
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file), #write to file 
                logging.StreamHandler()  # show in console
            ]
        )

        self.logger = logging.getLogger(__name__)
    
    def _setup_fastf1(self):
        """Initialize FastF1 with cache."""
        try:
            fastf1.Cache.enable_cache(str(self.cache_dir))
        except Exception as e:
            self.logger.error(f"Failed to initialize FastF1 cache: {e}")
            sys.exit(1)
    
    def fetch_qualifying_data(self, years):
        """
        Fetch qualifying data for specified years.
        
        Args:
            years (list): List of years to fetch data for
        """
        results = {'success': [], 'failed': []}
        
       
        for year in years:
            try:
                output_file = self.output_dir / f'qualifying_data_{year}.csv'
                    
                # Skip if file exists and reload is False
                if output_file.exists() and not self.reload:
                    self.logger.info(f"Data for {year} already exists, skipping...")
                    results['success'].append(year)
                    continue
                    
                # Get schedule for the year
                schedule = self._get_schedule(year)
                if schedule is None:
                    results['failed'].append(year)
                    continue
                    
                 # Process each event
                yearly_data = self._process_year_events(year, schedule)
                    
                if yearly_data:
                    # Save each year to CSV
                    yearly_df = pd.concat(yearly_data, ignore_index=True)
                    yearly_df.to_csv(output_file, index=False)
                        
                    results['success'].append(year)
                else:
                    results['failed'].append(year)
                        
            except Exception as e:
                self.logger.error(f"Failed to process {year}: {str(e)}")
                results['failed'].append(year)
            finally:
                gc.collect()  # Clear memory after each year
        
        return results
    
    def _get_schedule(self, year, max_retries=3, delay=5):
        """Get event schedule with retry logic."""
        for attempt in range(max_retries):
            try:
                schedule = fastf1.get_event_schedule(year)
                
                # Filter schedule
                schedule = schedule[schedule['EventFormat'] != 'testing']
                if datetime.now().year == year:
                    schedule = schedule[schedule['EventDate'] < datetime.now()]
                
                return schedule
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {year}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"Failed to get {year} schedule: {str(e)}")
                    return None
    
    def _process_year_events(self, year, schedule):
        """Process all events for a given year."""
        yearly_data = []
    
        for _, event in schedule.iterrows():
            try:
                time.sleep(2)  # attempt at rate limiting 
        
                session = fastf1.get_session(year, event['EventName'], 'Q')
                session.load()
        
                laps = session.laps #df of all quali laps in that session 
                weather_data = session.weather_data

                wet_compounds = {'INTERMEDIATE', 'WET'}

                # Determine if session is wet based on rainfall 
                is_wet = False

                if weather_data is not None and 'Rainfall' in weather_data.columns:
                    # Get the time range of session
                    session_start = laps['Time'].min()
                    session_end = laps['Time'].max()
                    
                    # Filter weather data to only include readings during the session
                    session_weather = weather_data[
                        (weather_data['Time'] >= session_start) & 
                        (weather_data['Time'] <= session_end)
                    ]
                    
                    # Calculate the percentage of weather readings that showed rainfall
                    if not session_weather.empty:
                        rain_percentage = session_weather['Rainfall'].mean() #proportion of True
                        is_wet = rain_percentage > 0.5  # True if more than 50% of session had rain
                       

                #map driver, number, position to laps df 
                driver_info = {}
                for _, driver in session.results.iterrows():  
                    driver_number = driver['DriverNumber']
                    driver_info[driver_number] = {
                        'BroadcastName': driver['BroadcastName'],
                        'Position': driver['Position'], # Add quali position
                    }
            
                laps['Driver'] = laps['DriverNumber'].map(lambda x: driver_info[x]['BroadcastName']) #gets corresponding name for every number and saves as Driver
                laps['QualifyingPosition'] = laps['DriverNumber'].map(lambda x: driver_info[x]['Position'])

                
                laps['Year'] = year
                laps['EventName'] = event['EventName']
                laps['WetSession'] = is_wet
        
                yearly_data.append(laps)

            except Exception as e:
                self.logger.error(
                    f"Error loading {event['EventName']} {year}: {str(e)}"
                )

        return yearly_data

def main():
    parser = argparse.ArgumentParser(description='Fetch F1 Quali Data')
    parser.add_argument('--years', nargs='+', type=int, required=True,
                      help='Years to fetch data for')
    parser.add_argument('--cache-dir', default='f1_cache',
                      help='Directory for FastF1 cache')
    parser.add_argument('--output-dir', default='data/original_data',
                      help='Directory for output files')
    parser.add_argument('--reload', default= False,
                      help='Reload existing data')
    
    args = parser.parse_args()
    
    fetcher = F1DataFetcher(
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        reload=args.reload
    )
    
    results = fetcher.fetch_qualifying_data(args.years)
    
    print("\nData Collection Summary:")
    print(f"Successfully processed years: {results['success']}")
    print(f"Failed years: {results['failed']}")

if __name__ == "__main__":
    main()