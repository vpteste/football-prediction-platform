from fastapi import FastAPI
from dotenv import load_dotenv
import os
import requests
import joblib
import pandas as pd
import json
from datetime import datetime, timedelta

# Charger les variables d'environnement
load_dotenv()

app = FastAPI()

# --- Chargement des modèles et du cache au démarrage ---
try:
    model = joblib.load("prediction_model.joblib")
    model_columns = joblib.load("model_columns.joblib")
    print("Modèle et colonnes chargés.")
    with open("feature_cache.json", 'r') as f:
        feature_cache = json.load(f)
    print("Cache de features chargé.")
except FileNotFoundError:
    print("Erreur critique: Un ou plusieurs fichiers sont manquants.")
    model, model_columns, feature_cache = None, None, None

# --- Configuration des APIs ---
FD_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
FD_HEADERS = {"X-Auth-Token": FD_API_KEY}

AF_API_KEY = os.getenv("API_FOOTBALL_KEY")
AF_HEADERS = {"x-apisports-key": AF_API_KEY}

RESULT_MAPPING = {"H": "Victoire à domicile", "D": "Match nul", "A": "Victoire à l'extérieur"}

def fetch_from_api_football():
    """Source de données secondaire : api-football.com"""
    print("Fallback: Tentative de récupération via api-football.com")
    if not AF_API_KEY:
        print("Clé API pour api-football.com non trouvée.")
        return []

    url = "https://v3.football.api-sports.io/fixtures"
    # Correspondance approximative des ligues majeures
    league_ids = [39, 61, 78, 135, 140, 2] # PL, Ligue 1, Bundesliga, Serie A, La Liga, Champions League
    all_matches_standardized = []

    for league_id in league_ids:
        try:
            params = {"league": league_id, "season": datetime.now().year - 1, "status": "NS"} # NS = Not Started
            response = requests.get(url, headers=AF_HEADERS, params=params)
            response.raise_for_status()
            api_response = response.json()['response']

            for fix in api_response:
                standardized_match = {
                    "id": fix['fixture']['id'],
                    "utcDate": fix['fixture']['date'],
                    "competition": {'name': fix['league']['name']},
                    "homeTeam": {'name': fix['teams']['home']['name']},
                    "awayTeam": {'name': fix['teams']['away']['name']}
                }
                all_matches_standardized.append(standardized_match)
        except Exception as e:
            print(f"Erreur avec api-football pour la ligue {league_id}: {e}")
            continue
    
    print(f"{len(all_matches_standardized)} matchs trouvés via api-football.com")
    return all_matches_standardized

def make_prediction(match):
    # ... (La fonction make_prediction reste la même)
    home_team_name = match.get('homeTeam', {}).get('name')
    away_team_name = match.get('awayTeam', {}).get('name')
    if not home_team_name or not away_team_name: return None
    home_features = feature_cache.get(home_team_name)
    away_features = feature_cache.get(away_team_name)
    if not home_features or not away_features: return None
    input_data = { 'home_form_pts': home_features['pts'], 'home_form_gs': home_features['gs'],
                   'home_form_ga': home_features['ga'], 'home_form_gd': home_features['gd'],
                   'away_form_pts': away_features['pts'], 'away_form_gs': away_features['gs'],
                   'away_form_ga': away_features['ga'], 'away_form_gd': away_features['gd'] }
    input_df = pd.DataFrame([input_data], columns=model_columns)
    prediction_result = model.predict(input_df)[0]
    prediction_proba = model.predict_proba(input_df)[0]
    confidence = max(prediction_proba)
    return {
        "id": match.get('id'), "match": f'{home_team_name} vs {away_team_name}',
        "prediction": RESULT_MAPPING.get(prediction_result, "Inconnu"),
        "confidence_raw": confidence, "confidence": f"{confidence:.0%}",
        "competition": match.get('competition'), "utcDate": match.get('utcDate')
    }

@app.get("/predictions")
def get_predictions():
    if not all([model, model_columns, feature_cache]):
        return {"error": "Modèle ou cache non chargé."}

    matches = []
    try:
        # 1. Essayer la source primaire : football-data.org
        print("Tentative de récupération via football-data.org")
        date_from = datetime.now().strftime('%Y-%m-%d')
        date_to = (datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d')
        url = "https://api.football-data.org/v4/matches"
        response = requests.get(url, headers=FD_HEADERS, params={"dateFrom": date_from, "dateTo": date_to})
        response.raise_for_status()
        matches = response.json().get('matches', [])
        print(f"football-data.org a retourné {len(matches)} matchs.")

        # 2. Si la source primaire échoue, utiliser le fallback
        if not matches:
            matches = fetch_from_api_football()

    except requests.exceptions.RequestException as e:
        print(f"Erreur avec football-data.org: {e}. Tentative de fallback.")
        matches = fetch_from_api_football()
    
    # --- Logique de prédiction et de tri (commune aux deux sources) ---
    all_predictions = []
    for match in matches:
        prediction = make_prediction(match)
        if prediction:
            all_predictions.append(prediction)

    top_10_predictions = sorted(all_predictions, key=lambda p: p['confidence_raw'], reverse=True)[:10]
    print(f"{len(top_10_predictions)} prédictions à haute confiance sélectionnées.")
    return {"predictions": top_10_predictions}
