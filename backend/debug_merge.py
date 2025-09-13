import pandas as pd
import os
from thefuzz import process

def smart_debug_team_name_mismatches():
    """
    Uses fuzzy matching to find the best potential match for mismatched team names.
    """
    # --- 1. Load Historical Data ---
    historical_data_path = "backend/historical_data.csv"
    if not os.path.exists(historical_data_path):
        print(f"Error: {historical_data_path} not found.")
        return
    main_df = pd.read_csv(historical_data_path)
    # Use a clean, unique set of team names from the main dataset
    main_teams = sorted(list(set(main_df['home_team'].unique()).union(set(main_df['away_team'].unique()))))

    # --- 2. Load Odds Data ---
    odds_dir = "backend/odds_data"
    if not os.path.exists(odds_dir):
        print(f"Error: Odds directory {odds_dir} not found.")
        return

    all_odds_dfs = []
    for filename in os.listdir(odds_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(odds_dir, filename)
            try:
                odds_df = pd.read_csv(filepath, encoding='latin1')
                all_odds_dfs.append(odds_df)
            except Exception:
                continue
    
    if not all_odds_dfs:
        print("No odds files found.")
        return

    odds_master_df = pd.concat(all_odds_dfs, ignore_index=True)
    odds_teams = sorted(list(set(odds_master_df['HomeTeam'].dropna().unique()).union(set(odds_master_df['AwayTeam'].dropna().unique()))))

    # --- 3. Find Best Matches for Odds Teams ---
    print("--- Suggested Mappings for Team Names ---")
    print("# Format: \"Odds File Name\": \"Historical Data Name\",")
    
    suggested_map = {}
    for odds_team in odds_teams:
        # Find the best match from the list of historical team names
        best_match, score = process.extractOne(odds_team, main_teams)
        
        # If the match is not perfect but the score is high, suggest it.
        # If the names are already identical, we don't need a map entry.
        if odds_team != best_match and score > 80: # Using a threshold of 80
            suggested_map[odds_team] = best_match

    # Print the suggested map in a copy-paste friendly format
    for key, value in suggested_map.items():
        print(f'    "{key}": "{value}",')

if __name__ == "__main__":
    smart_debug_team_name_mismatches()