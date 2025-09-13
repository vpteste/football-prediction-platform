import pandas as pd
import pytest
from backend.predictor import get_h2h_stats_for_prediction
from backend.trainer import add_result_column

def test_get_h2h_stats_for_prediction(sample_dataframe):
    """Tests the get_h2h_stats_for_prediction function."""
    # The function needs the 'result' column
    df = add_result_column(sample_dataframe)

    # Test for a matchup that exists (Team A vs Team B)
    h2h_stats = get_h2h_stats_for_prediction('Team A', 'Team B', df)
    
    # In the sample data:
    # Match 0: A vs B, 1-1 (Draw)
    # Match 2: B vs A, 2-2 (Draw)
    # Total: 2 matches, 2 draws.
    # Goals for A: 1 (home) + 2 (away) = 3. Avg = 1.5
    # Goals for B: 1 (away) + 2 (home) = 3. Avg = 1.5
    assert h2h_stats['h2h_home_win_ratio'] == 0.0 # From Team A's perspective
    assert h2h_stats['h2h_away_win_ratio'] == 0.0
    assert h2h_stats['h2h_draw_ratio'] == 1.0
    assert h2h_stats['h2h_avg_goals_for_home'] == 1.5
    assert h2h_stats['h2h_avg_goals_for_away'] == 1.5

    # Test for a matchup that does not exist
    h2h_stats_new = get_h2h_stats_for_prediction('Team X', 'Team Y', df)
    assert h2h_stats_new['h2h_home_win_ratio'] == 0.0
