import pandas as pd
import os

def aggregate_team_stats():
    """
    Reads player statistics from various CSV files in the dataset directory,
    aggregates them by club, and saves the result to a new CSV file.
    """
    dataset_path = "dataset/"
    files_to_process = {
        'attacking.csv': ['assists', 'corner_taken', 'offsides', 'dribbles'],
        'defending.csv': ['balls_recoverd', 'tackles', 't_won', 'clearance_attempted'],
        'disciplinary.csv': ['fouls_committed', 'fouls_suffered', 'red', 'yellow'],
        'goals.csv': ['goals', 'penalties', 'free_kicks'],
        'attempts.csv': ['shots', 'on_target', 'off_target', 'blocked'],
        'key_stats.csv': ['threat', 'influence', 'creativity', 'total_points'],
        'distributon.csv': ['pass_accuracy', 'pass_complete', 'pass_incomplete', 'cross_accuracy', 'cross_complete', 'cross_incomplete']
    }

    # Standardize team names
    team_name_map = {
        "Man. United": "Manchester United",
        "Man. City": "Manchester City",
        "Paris": "Paris Saint-Germain",
        "LOSC": "Lille",
        # Add other mappings as needed
    }

    all_stats = []

    for filename, cols in files_to_process.items():
        filepath = os.path.join(dataset_path, filename)
        if os.path.exists(filepath):
            print(f"Processing {filepath}...")
            try:
                df = pd.read_csv(filepath)
                # Drop player-specific columns before grouping
                df = df.drop(columns=['serial', 'player_name', 'position', 'match_played'], errors='ignore')
                
                # Standardize club names
                df['club'] = df['club'].replace(team_name_map)

                # Group by club and calculate the mean for the relevant columns
                # Ensure columns exist before trying to aggregate
                agg_cols = [col for col in cols if col in df.columns]
                if 'club' in df.columns and agg_cols:
                    club_stats = df.groupby('club')[agg_cols].mean()
                    # Add prefix to column names to identify source file
                    prefix = filename.split('.')[0]
                    club_stats = club_stats.add_prefix(f"{prefix}_")
                    all_stats.append(club_stats)
            except Exception as e:
                print(f"  Could not process {filepath}: {e}")
        else:
            print(f"File not found: {filepath}")

    if not all_stats:
        print("No statistics were aggregated.")
        return

    # Merge all aggregated stats into a single DataFrame
    final_agg_df = pd.concat(all_stats, axis=1)

    # Fill NaN values with the mean of the column
    for col in final_agg_df.columns:
        final_agg_df[col] = final_agg_df[col].fillna(final_agg_df[col].mean())

    output_path = "backend/team_aggregated_stats.csv"
    final_agg_df.to_csv(output_path)
    print(f"\nSuccessfully aggregated team stats to {output_path}")

if __name__ == "__main__":
    aggregate_team_stats()
