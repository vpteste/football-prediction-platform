import pandas as pd
import os
import re
from datetime import datetime

def import_and_standardize_data(base_path="backend/csv_data/full_dataset"):
    """
    Imports and standardizes data from multiple CSV files into a single DataFrame.
    """
    all_data = []
    print(f"Starting data import from: {base_path}")

    for filename in os.listdir(base_path):
        if filename.endswith(".csv"):
            filepath = os.path.join(base_path, filename)
            print(f"  Processing: {filepath}")
            try:
                df = pd.read_csv(filepath, encoding='latin1')

                # Standardize column names
                rename_map = {
                    'Date': 'date',
                    'HomeTeam': 'home_team',
                    'AwayTeam': 'away_team',
                    'FTHG': 'home_goals',
                    'FTAG': 'away_goals',
                    'Div': 'competition'
                }
                df = df.rename(columns=rename_map)

                # Robust date parsing
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
                
                # Extract season from filename
                season_match = re.search(r'(\d{4})', filename)
                if season_match:
                    year1_str = season_match.group(1)[:2]
                    year2_str = season_match.group(1)[2:]
                    df['season'] = f"20{year1_str}-20{year2_str}"
                else:
                    df['season'] = 'Unknown'

                required_cols = ['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'competition', 'season']
                
                # Select only the required columns if they exist
                existing_cols = [col for col in required_cols if col in df.columns]
                df = df[existing_cols]

                if all(col in df.columns for col in required_cols):
                    df = df.dropna(subset=['date', 'home_team', 'away_team', 'home_goals', 'away_goals'])
                    all_data.append(df)
                else:
                    print(f"  Skipping {filepath} due to missing one of the required columns.")

            except Exception as e:
                print(f"  Error processing {filepath}: {e}")
                continue

    if not all_data:
        print("\nNo data found or processed.")
        return None

    final_df = pd.concat(all_data, ignore_index=True)
    final_df['date'] = pd.to_datetime(final_df['date'])
    final_df = final_df.drop_duplicates(subset=['date', 'home_team', 'away_team'])
    final_df = final_df.sort_values('date').reset_index(drop=True)

    output_path = "backend/historical_data.csv"
    final_df.to_csv(output_path, index=False)
    print(f"\nSuccessfully imported and consolidated {len(final_df)} matches to {output_path}")
    return final_df

if __name__ == "__main__":
    import_and_standardize_data()
