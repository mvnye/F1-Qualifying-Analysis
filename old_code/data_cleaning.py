
from pathlib import Path
import numpy as np
import argparse



class F1DataCleaner:
    def __init__(self, input_dir='data/original_data', output_dir='data'):
        """
        Initialize F1 data cleaner.
        
        Args:
            years (list): List of years to process
            input_dir (str): Directory containing raw CSV files
            output_dir (str): Directory for cleaned output files
        """
        #self.years = years
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        
    def combine_data(self):
        dfs = []

        for file in self.input_dir.glob('*.csv'):
            orig_df = pd.read_csv(file, index_col = 0)
            print(f"Reading {file.name}")
            cleaned_df = orig_df[(orig_df['Deleted'] == False) & #lap not deleted
                       # (orig_df['TrackStatus'] == 1) & #normal conditions
                        (orig_df['IsAccurate'] == True)] #actual data
            cleaned_df = cleaned_df.dropna(axis=1, how='all') #remove empty columns 
            cleaned_df = cleaned_df.drop(columns = ['IsAccurate', 'FastF1Generated', 
                                             'Deleted', 'LapStartDate']) #remove not needed columns
            dfs.append(cleaned_df)

        combined = pd.concat(dfs, ignore_index = True)
        combined = combined.rename(columns = {'Time': 'LapCompletionTime'}) 

        combined = combined.sort_values(by=['Year', 'EventName', 'Driver', 'LapNumber'])

        return combined
    
    def change_time_format(self, df):
        
        time_columns = [
            'LapCompletionTime', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time', 
            'LapStartTime', 'Sector1SessionTime', 'Sector2SessionTime', 'Sector3SessionTime'
            ]
        for col in time_columns:
            if col in df.columns:  # Check if column exists
                if df[col].dtype == 'object':  # Check if column contains strings
                    df[col] = df[col].str.replace('0 days ', '')

        lap_columns = ['LapTime']
        sector_columns = ['Sector1Time', 'Sector2Time', 'Sector3Time']
        session_columns = ['LapStartTime', 'LapCompletionTime', 'Sector1SessionTime', 'Sector2SessionTime', 'Sector3SessionTime']

        for col in lap_columns:
            if col in df.columns: #check to make sure exists and there we no issues in data collection
                df[col] = pd.to_timedelta(df[col]).dt.total_seconds().round(3)
                # Convert to MM:SS.mmm format
                df[col] = df[col].apply(lambda x: f"{int(x//60):01d}:{x%60:06.3f}" if pd.notnull(x) else None)

        for col in sector_columns:
            if col in df.columns:
                df[col] = pd.to_timedelta(df[col]).dt.total_seconds().round(3)
                # Convert to SS.mmm format
                df[col] = df[col].apply(lambda x: f"{x:06.3f}" if pd.notnull(x) else None)
                new_col_name = f"{col} (s)"
                df = df.rename(columns={col: new_col_name})

        for col in session_columns:
            if col in df.columns:
                # Keep these as timestamps for ordering laps in session 
                df[col] = pd.to_datetime(df[col], format='mixed')
                df[col] = df[col].dt.time #only show time, not date 
        
        speed_columns = ['SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST']

        for col in speed_columns:
            if col in df.columns:
                new_col_name = f"{col}(km/h)"
                df = df.rename(columns={col: new_col_name})
        
        return df
        
    
    def clean_data(self):
        """
        Main method to clean data.
        
        Args:
    
        """
        try:
            combined_data = self.combine_data()
            earliest_year = sorted(combined_data['Year'].unique())[0]
            latest_year = sorted(combined_data['Year'].unique())[-1]

            output_file = self.output_dir / f'quali_data_{earliest_year}_to_{latest_year}.csv'
            #cleaned_combined_data = self.change_time_format(combined_data)
            #cleaned_combined_data.to_csv(output_file, index = False) ##check this 
            combined_data.to_csv(output_file, index = False)
            return {'success': True, 'message': f"Data saved to {output_file}"}
        except Exception as e:
            return {'success': False, 'message': f"Failed to clean data: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description='Clean Data')
    #parser.add_argument('--years', nargs='+', type=int, required=True,
                      #help='Years to clean datafor')
    parser.add_argument('--input-dir', default='data/original_data',
                      help='Directory for input files')
    parser.add_argument('--output-dir', default='data',
                      help='Directory for output files')
    
    args = parser.parse_args()
    
    cleaner = F1DataCleaner(
       #years = args.years,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
    )
    
    results = cleaner.clean_data()
    
    if results['success']:
        print("\nSuccessfully Combined and Cleaned Data")
        print(results['message'])
    else:
        print("\nError occurred:")
        print(results['message'])

if __name__ == "__main__":
    main()