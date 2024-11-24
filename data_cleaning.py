import pandas as pd
import fastf1
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

        #fulltime_drivers = ['BOT', 'HAM', 'VER', 'NOR', 'ALB', 'PER', 'LEC', 'SAI', 'STR', 'RIC', 
                            #'VET', 'GAS', 'KVY', 'OCO', 'GRO', 'MAG', 'RUS', 'GIO', 'RAI', 'LAT', 
                            #'HUL', 'ALO', 'TSU', 'MAZ', 'MSC','KUB', 'ZHO', 'SAR', 'PIA', 'DEV', 
                            #'LAW', 'COL', 'HAR','VAN', 'ERI', 'SIR']

        for file in self.input_dir.glob('*.csv'):
            orig_df = pd.read_csv(file, index_col = 0)
            print(f"Reading {file.name}")
            cleaned_df = orig_df[(orig_df['Deleted'] == False) & #lap not deleted
                        (orig_df['TrackStatus'] == 1) & #normal conditions
                         #(orig_df['Driver'].isin(fulltime_drivers)) & #full time 
                        (orig_df['IsAccurate'] == True)] #actual data
            cleaned_df = cleaned_df.dropna(axis=1, how='all') #remove empty columns 
            cleaned_df = cleaned_df.drop(columns = ['IsAccurate', 'FastF1Generated', 
                                            'TrackStatus', 'Deleted']) #remove not needed columns
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
            cleaned_combined_data = self.change_time_format(combined_data)
            cleaned_combined_data.to_csv(output_file, index = False) ##check this 
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