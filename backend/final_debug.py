import pandas as pd
import os

def final_debug_team_lists():
    """
    Prints the complete, sorted, unique team lists from both the historical data and the odds data.
    """
    # --- 1. Load Historical Data ---
    historical_data_path = "backend/historical_data.csv"
    if not os.path.exists(historical_data_path):
        print(f"Error: {historical_data_path} not found.")
        return
    main_df = pd.read_csv(historical_data_path)
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

    # --- 3. Print Both Lists ---
    print("--- Teams in Historical Data (historical_data.csv) ---")
    for team in main_teams:
        print(team)
    
    print("\n--- Teams in Odds Data (football-data.co.uk) ---")
    for team in odds_teams:
        print(team)

if __name__ == "__main__":
    final_debug_team_lists()
