import pandas as pd
import pytest

@pytest.fixture
def sample_dataframe():
    """Provides a sample dataframe for testing feature engineering."""
    data = {
        'date': pd.to_datetime(['2023-01-01', '2023-01-01', '2023-01-08', '2023-01-08']),
        'home_team': ['Team A', 'Team C', 'Team B', 'Team D'],
        'away_team': ['Team B', 'Team D', 'Team A', 'Team C'],
        'home_goals': [1, 0, 2, 3],
        'away_goals': [1, 0, 2, 1]
    }
    df = pd.DataFrame(data)
    return df
