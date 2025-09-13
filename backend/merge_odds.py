import pandas as pd
import os

def merge_odds_with_historical_data():
    """
    Merges the downloaded odds data with the main historical match data.
    """
    # --- 1. Load Historical Data ---
    historical_data_path = "backend/historical_data.csv"
    if not os.path.exists(historical_data_path):
        print(f"Error: {historical_data_path} not found.")
        return

    print("Loading historical match data...")
    main_df = pd.read_csv(historical_data_path)
    main_df['date'] = pd.to_datetime(main_df['date'])

    # --- 2. Load and Concatenate Odds Data ---
    odds_dir = "backend/odds_data"
    if not os.path.exists(odds_dir):
        print(f"Error: Odds directory {odds_dir} not found.")
        return

    all_odds_dfs = []
    print("Loading and processing downloaded odds files...")
    for filename in os.listdir(odds_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(odds_dir, filename)
            try:
                odds_df = pd.read_csv(filepath, encoding='latin1')
                odds_cols = ['Date', 'HomeTeam', 'AwayTeam', 'B365H', 'B365D', 'B365A', 'PSH', 'PSD', 'PSA']
                if all(col in odds_df.columns for col in odds_cols):
                    odds_df = odds_df[odds_cols]
                    odds_df.columns = ['date', 'home_team', 'away_team', 'b365h', 'b365d', 'b365a', 'psh', 'psd', 'psa']
                    odds_df['date'] = pd.to_datetime(odds_df['date'], dayfirst=True, errors='coerce')
                    all_odds_dfs.append(odds_df)
            except Exception as e:
                print(f"  - Error processing {filename}: {e}")

    if not all_odds_dfs:
        print("No valid odds data was loaded.")
        return

    odds_master_df = pd.concat(all_odds_dfs, ignore_index=True)
    odds_master_df.dropna(subset=['date', 'home_team', 'away_team'], inplace=True)
    print(f"Loaded a total of {len(odds_master_df)} matches from odds files.")

    # --- 3. Standardize Team Names ---
    team_name_map = {
        "Alaves": "Alavés", "Almeria": "Almería", "Arsenal": "Arsenal FC",
        "Aston Villa": "Aston Villa FC", "Ath Bilbao": "Athletic Club", "Ath Madrid": "Atletico Madrid",
        "Bournemouth": "AFC Bournemouth", "Brentford": "Brentford FC", "Brighton": "Brighton & Hove Albion FC",
        "Burnley": "Burnley FC", "Cadiz": "Cádiz", "Celta": "Celta Vigo",
        "Chelsea": "Chelsea FC", "Crystal Palace": "Crystal Palace FC", "Everton": "Everton FC",
        "Fulham": "Fulham FC", "La Coruna": "Deportivo La Coruna", "Leeds": "Leeds United FC",
        "Leicester": "Leicester City FC", "Liverpool": "Liverpool FC", "Luton": "Luton Town FC",
        "Man City": "Manchester City FC", "Man United": "Manchester United FC", "Newcastle": "Newcastle United FC",
        "Norwich": "Norwich City FC", "Nott'm Forest": "Nottingham Forest FC", "Sheffield United": "Sheffield United FC",
        "Southampton": "Southampton FC", "Spurs": "Tottenham Hotspur FC", "Tottenham": "Tottenham Hotspur FC",
        "Watford": "Watford FC", "West Brom": "West Bromwich Albion FC", "West Ham": "West Ham United FC",
        "Wolves": "Wolverhampton Wanderers FC", "Leganes": "Leganés", "Betis": "Real Betis",
        "Paris SG": "Paris Saint-Germain", "St Etienne": "AS Saint-Etienne",
        "M'gladbach": "Borussia Monchengladbach", "Ein Frankfurt": "Eintracht Frankfurt", "FC Koln": "1. FC Koln",
        "Hertha": "Hertha BSC", "Leverkusen": "Bayer 04 Leverkusen", "Mainz": "1. FSV Mainz 05",
        "RB Leipzig": "RB Leipzig", "Schalke 04": "FC Schalke 04", "Stuttgart": "VfB Stuttgart",
        "Union Berlin": "1. FC Union Berlin", "Werder Bremen": "SV Werder Bremen", "Wolfsburg": "VfL Wolfsburg",
        "Inter": "Inter Milan", "Milan": "AC Milan", "Roma": "AS Roma", "Verona": "Hellas Verona",
        "Spal": "SPAL"
    }
    
    print("Standardizing team names...")
    odds_master_df['home_team'] = odds_master_df['home_team'].replace(team_name_map)
    odds_master_df['away_team'] = odds_master_df['away_team'].replace(team_name_map)

    # --- 4. Merge DataFrames ---
    print("Merging historical data with odds data...")
    merged_df = pd.merge(main_df, odds_master_df, on=['date', 'home_team', 'away_team'], how='left')

    # --- 5. Save Final Dataset ---
    output_path = "backend/historical_data_with_odds.csv"
    merged_df.to_csv(output_path, index=False)
    
    num_matches_with_odds = merged_df['b365h'].notna().sum()
    print(f"\nSuccessfully merged data. Final dataset has {len(merged_df)} rows.")
    print(f"{num_matches_with_odds} matches now have odds information.")
    print(f"Enriched data saved to {output_path}")

if __name__ == "__main__":
    merge_odds_with_historical_data()