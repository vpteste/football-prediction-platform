import pandas as pd
import pytest
from backend.trainer import add_result_column, create_features, add_h2h_features

def test_add_result_column():
    # Create a sample dataframe
    data = {
        'home_goals': [1, 2, 3],
        'away_goals': [0, 2, 4]
    }
    df = pd.DataFrame(data)

    # Apply the function
    df = add_result_column(df)

    # Check the results
    expected_results = ['H', 'D', 'A']
    assert 'result' in df.columns
    assert df['result'].tolist() == expected_results

def test_create_features(sample_dataframe):
    """Tests the create_features function."""
    df = add_result_column(sample_dataframe)
    
    # The create_features function expects the 'result' column to exist
    # and also does some in-place modifications.
    df_featured, form_cols = create_features(df.copy()) # Use copy to avoid side effects

    assert len(form_cols) == 12 # Check if all form columns are returned
    
    # Check for a specific calculated value
    # For the 3rd match (index 2), Team B (home) played Team A (away)
    # Team A's first match was a draw (1-1) vs Team B. So 1 point, 1 GS, 1 GA.
    # Team B's first match was a draw (1-1) vs Team A. So 1 point, 1 GS, 1 GA.
    # The form is calculated based on past matches.
    # So for the 3rd match, away_form_pts for Team A should be 1.0
    # Let's check the value for away_form_pts for the match at index 2
    assert df_featured.loc[2, 'away_form_pts'] == 1.0
    assert df_featured.loc[2, 'home_form_pts'] == 1.0
    assert df_featured.loc[2, 'diff_form_pts'] == 0.0

    # For the 4th match (index 3), Team D (home) vs Team C (away)
    # Team C's first match was a draw (0-0) vs Team D. 1 pt, 0 GS, 0 GA.
    # Team D's first match was a draw (0-0) vs Team C. 1 pt, 0 GS, 0 GA.
    # So for the 4th match, home_form_pts for Team D should be 1.0
    assert df_featured.loc[3, 'home_form_pts'] == 1.0
    assert df_featured.loc[3, 'away_form_pts'] == 1.0

def test_add_h2h_features(sample_dataframe):
    """Tests the add_h2h_features function."""
    df = add_result_column(sample_dataframe)
    
    df_h2h, h2h_cols = add_h2h_features(df.copy())

    assert len(h2h_cols) == 5

    # For the 3rd match (index 2), Team B vs Team A
    # Their first encounter was at index 0, a 1-1 draw.
    # So, for this match, the H2H stats should reflect that one draw.
    # Total matches = 1. home_wins = 0, away_wins = 0, draws = 1.
    # From Team B's perspective (home team):
    # h2h_home_win_ratio should be 0
    # h2h_away_win_ratio should be 0
    # h2h_draw_ratio should be 1
    assert df_h2h.loc[2, 'h2h_home_win_ratio'] == 0.0
    assert df_h2h.loc[2, 'h2h_away_win_ratio'] == 0.0
    assert df_h2h.loc[2, 'h2h_draw_ratio'] == 1.0
    assert df_h2h.loc[2, 'h2h_avg_goals_for_home'] == 1.0 # Team B scored 1 goal
    assert df_h2h.loc[2, 'h2h_avg_goals_for_away'] == 1.0 # Team A scored 1 goal

    # For the first match (index 0), there are no past H2H stats
    assert df_h2h.loc[0, 'h2h_home_win_ratio'] == 0.0
