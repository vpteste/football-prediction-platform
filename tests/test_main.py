from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_teams():
    """Tests the /teams endpoint."""
    response = client.get("/teams")
    assert response.status_code == 200
    data = response.json()
    assert "teams" in data
    assert isinstance(data["teams"], list)
    # The sample data in historical_data.csv has many teams, so it should not be empty
    assert len(data["teams"]) > 0

def test_predict_endpoint():
    """Tests the /predict endpoint."""
    payload = {"home_team": "Werder Bremen", "away_team": "Borussia Dortmund"}
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "probabilities" in data
    assert "score" in data
    assert "away_win" in data["probabilities"]
    assert "draw" in data["probabilities"]
    assert "home_win" in data["probabilities"]