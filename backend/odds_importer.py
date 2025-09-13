import requests
import os

def download_odds_data():
    """
    Downloads historical football odds data from football-data.co.uk for major leagues.
    """
    BASE_URL = "https://www.football-data.co.uk/mmz4281/"
    # Seasons from 2019-20 to 2023-24
    SEASONS = [f"{i:02d}{i+1:02d}" for i in range(19, 24)] 
    # League codes for England, Spain, Germany, Italy, France
    LEAGUE_CODES = ["E0", "SP1", "D1", "I1", "F1"]

    output_dir = "backend/odds_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    for season in SEASONS:
        for league in LEAGUE_CODES:
            url = f"{BASE_URL}{season}/{league}.csv"
            filename = f"{season}_{league}.csv"
            filepath = os.path.join(output_dir, filename)
            
            try:
                print(f"Downloading data for {league} in season 20{season[:2]}/20{season[2:]} from {url}...")
                response = requests.get(url)
                response.raise_for_status() # Raise an exception for bad status codes

                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"  -> Successfully saved to {filepath}")

            except requests.exceptions.RequestException as e:
                print(f"  -> Failed to download {url}. Reason: {e}")
                # Clean up empty file if download failed
                if os.path.exists(filepath) and os.path.getsize(filepath) == 0:
                    os.remove(filepath)
            except Exception as e:
                print(f"  -> An unexpected error occurred: {e}")

if __name__ == "__main__":
    download_odds_data()
