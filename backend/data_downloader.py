import requests
import os

def download_historical_data():
    """
    Downloads historical football match and odds data from football-data.co.uk.
    """
    BASE_URL = "https://www.football-data.co.uk/mmz4281/"
    # Seasons from 2014-15 to 2023-24
    SEASONS = [f"{i:02d}{i+1:02d}" for i in range(14, 24)] 
    # League codes for England, Spain, Germany, Italy, France
    LEAGUE_CODES = ["E0", "SP1", "D1", "I1", "F1"]

    # --- Create Directories ---
    odds_output_dir = "backend/odds_data"
    hist_output_dir = "backend/csv_data/full_dataset"
    if not os.path.exists(odds_output_dir):
        os.makedirs(odds_output_dir)
        print(f"Created directory: {odds_output_dir}")
    if not os.path.exists(hist_output_dir):
        os.makedirs(hist_output_dir)
        print(f"Created directory: {hist_output_dir}")

    # --- Download Data ---
    for season in SEASONS:
        for league in LEAGUE_CODES:
            url = f"{BASE_URL}{season}/{league}.csv"
            # Save to both directories. The file contains both historical data and odds.
            hist_filename = f"{season}_{league}_hist.csv"
            odds_filename = f"{season}_{league}_odds.csv"
            hist_filepath = os.path.join(hist_output_dir, hist_filename)
            odds_filepath = os.path.join(odds_output_dir, odds_filename)
            
            try:
                print(f"Downloading data for {league} in season 20{season[:2]}/20{season[2:]} from {url}...")
                response = requests.get(url)
                response.raise_for_status() # Raise an exception for bad status codes

                # Write the same content to two different conceptual locations
                with open(hist_filepath, 'wb') as f:
                    f.write(response.content)
                with open(odds_filepath, 'wb') as f:
                    f.write(response.content)
                print(f"  -> Successfully saved to {hist_filepath} and {odds_filepath}")

            except requests.exceptions.RequestException as e:
                print(f"  -> Failed to download {url}. Reason: {e}")

if __name__ == "__main__":
    download_historical_data()
