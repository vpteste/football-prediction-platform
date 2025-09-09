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

# --- Configuration ---
RESULT_MAPPING = {"H": "Victoire à domicile", "D": "Match nul", "A": "Victoire à l'extérieur"}

def fetch_matches_via_espn_api():
    """Récupère les matchs à venir en utilisant l'API interne d'ESPN."""
    print("Lancement du Scraper API pour récupérer les matchs à venir...")
    matches = []
    try:
        # On récupère les matchs pour les 7 prochains jours
        date_to = (datetime.now() + timedelta(days=7)).strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/v2/scores/soccer/all/scoreboard/dates/{datetime.now().strftime('%Y%m%d')}-{date_to}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        for event in data.get('events', []):
            competition_data = event.get('competitions', [{}])[0]
            competition_name = competition_data.get('name', 'Compétition Inconnue')
            
            full_event_name = event.get('name', '')
            teams = full_event_name.split(' vs ')
            if len(teams) != 2:
                continue
            home_team, away_team = teams

            standardized_match = {
                "id": event.get('id'),
                "utcDate": event.get('date'),
                "competition": {'name': competition_name},
                "homeTeam": {'name': home_team},
                "awayTeam": {'name': away_team}
            }
            matches.append(standardized_match)

    except Exception as e:
        print(f"Erreur lors du scraping de l'API d'ESPN: {e}")
        return []

    print(f"{len(matches)} matchs trouvés via l'API d'ESPN.")
    return matches

def make_prediction(match):
    """Génère une prédiction pour un seul match."""
    home_team_name = match.get('homeTeam', {}).get('name')
    away_team_name = match.get('awayTeam', {}).get('name')
    if not home_team_name or not away_team_name: return None

    # Utiliser une table de correspondance si nécessaire (à créer)
    # home_team_name = TEAM_NAME_MAP.get(home_team_name, home_team_name)
    # away_team_name = TEAM_NAME_MAP.get(away_team_name, away_team_name)

    home_features = feature_cache.get(home_team_name)
    away_features = feature_cache.get(away_team_name)
    if not home_features or not away_features:
        print(f"Features non trouvées pour: '{home_team_name}' ou '{away_team_name}'")
        return None

    # Création des features différentielles comme pour l'entraînement
    input_data = {
        'diff_form_pts': home_features.get('pts', 0) - away_features.get('pts', 0),
        'diff_form_gs': home_features.get('gs', 0) - away_features.get('gs', 0),
        'diff_form_ga': home_features.get('ga', 0) - away_features.get('ga', 0),
        'diff_form_gd': home_features.get('gd', 0) - away_features.get('gd', 0)
    }
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

    matches = fetch_matches_via_espn_api()
    
    all_predictions = []
    for match in matches:
        prediction = make_prediction(match)
        if prediction:
            all_predictions.append(prediction)

    top_10_predictions = sorted(all_predictions, key=lambda p: p['confidence_raw'], reverse=True)[:10]
    print(f"{len(top_10_predictions)} prédictions à haute confiance sélectionnées.")
    return {"predictions": top_10_predictions}
