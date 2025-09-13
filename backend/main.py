from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests
import joblib
import pandas as pd
import json
from datetime import datetime, timedelta
from .predictor import predict_outcome_and_score
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

app = FastAPI()

# --- Définir les chemins absolus ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTCOME_MODEL_PATH = os.path.join(BASE_DIR, "outcome_model.joblib")
HOME_MODEL_PATH = os.path.join(BASE_DIR, "home_goals_model.joblib")
AWAY_MODEL_PATH = os.path.join(BASE_DIR, "away_goals_model.joblib")
COLUMNS_PATH = os.path.join(BASE_DIR, "model_columns.joblib")
HISTORICAL_DATA_PATH = os.path.join(BASE_DIR, "historical_data.csv")
LOGO_MAP_PATH = os.path.join(BASE_DIR, "team_logo_map.json")
TEAM_ID_MAP_PATH = os.path.join(BASE_DIR, "team_id_map.json")
DAILY_PREDICTIONS_PATH = os.path.join(BASE_DIR, "daily_predictions.json")
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, "label_encoder.joblib")

def add_result_column(df):
    """Adds the 'result' column (H/A/D) to the dataframe."""
    df["result"] = df.apply(lambda row: "H" if row["home_goals"] > row["away_goals"] else ("A" if row["away_goals"] > row["home_goals"] else "D"), axis=1)
    return df

# --- Chargement des modèles et des données au démarrage ---
try:
    outcome_model = joblib.load(OUTCOME_MODEL_PATH)
    home_model = joblib.load(HOME_MODEL_PATH)
    away_model = joblib.load(AWAY_MODEL_PATH)
    model_columns = joblib.load(COLUMNS_PATH)
    historical_data = pd.read_csv(HISTORICAL_DATA_PATH)
    historical_data['date'] = pd.to_datetime(historical_data['date'])
    historical_data = add_result_column(historical_data) # Add this line
    logger.info("Modèles, colonnes et données historiques chargés.")
    with open(LOGO_MAP_PATH, 'r') as f:
        logo_map = json.load(f)
    logger.info("Carte des logos chargée.")
    with open(TEAM_ID_MAP_PATH, 'r') as f:
        team_id_map = json.load(f)
    logger.info("Carte des IDs d'équipes chargée.")
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    logger.info("Label encoder chargé.")
except FileNotFoundError as e:
    logger.error(f"Erreur critique: Fichier manquant - {e}")
    outcome_model, home_model, away_model, model_columns, historical_data, logo_map, team_id_map, label_encoder = None, None, None, None, None, None, None, None

# --- Configuration ---
RESULT_MAPPING = {"H": "Victoire à domicile", "D": "Match nul", "A": "Victoire à l'extérieur"}
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

# --- Pydantic Model for Prediction Input ---
class MatchPredictionRequest(BaseModel):
    home_team: str
    away_team: str

def fetch_daily_matches_from_football_data():
    """Récupère les matchs pour les 7 prochains jours depuis football-data.org."""
    logger.info("Récupération des matchs pour les 7 prochains jours depuis football-data.org...")
    matches = []
    if not FOOTBALL_DATA_API_KEY:
        logger.error("Clé API pour football-data.org non configurée.")
        return matches

    headers = {'X-Auth-Token': FOOTBALL_DATA_API_KEY}
    date_from = datetime.now().strftime('%Y-%m-%d')
    date_to = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"http://api.football-data.org/v4/matches?dateFrom={date_from}&dateTo={date_to}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        for match in data.get('matches', []):
            standardized_match = {
                "id": match.get('id'),
                "utcDate": match.get('utcDate'),
                "competition": {'name': match.get('competition', {}).get('name', 'N/A')},
                "homeTeam": {'name': match.get('homeTeam', {}).get('name')},
                "awayTeam": {'name': match.get('awayTeam', {}).get('name')}
            }
            matches.append(standardized_match)

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de la récupération des matchs depuis football-data.org: {e}")
        return []

    logger.info(f"{len(matches)} matchs trouvés.")
    return matches

def update_daily_predictions():
    """Tâche planifiée pour mettre à jour les prédictions quotidiennes."""
    logger.info("Mise à jour des prédictions quotidiennes...")
    if not all([outcome_model, home_model, away_model, model_columns, historical_data is not None, label_encoder is not None]):
        logger.warning("Un ou plusieurs modèles ou données sont manquants, mise à jour annulée.")
        return

    matches = fetch_daily_matches_from_football_data()
    matches.sort(key=lambda x: x['utcDate'])
    all_predictions = []

    for match in matches:
        home_team_name = match.get('homeTeam', {}).get('name')
        away_team_name = match.get('awayTeam', {}).get('name')

        if not home_team_name or not away_team_name:
            logger.warning(f"Nom d'équipe manquant pour le match ID {match.get('id')}, saut.")
            continue
        
        logger.info(f"Traitement du match: {home_team_name} vs {away_team_name}")

        try:
            outcome, probabilities, home_goals, away_goals = predict_outcome_and_score(
                home_team_name, away_team_name, historical_data, 
                outcome_model, home_model, away_model, model_columns, 
                label_encoder
            )
            
            confidence = max(probabilities.values())

            all_predictions.append({
                "id": match.get('id'),
                "match": f'{home_team_name} vs {away_team_name}',
                "prediction": RESULT_MAPPING.get(outcome, "Inconnu"),
                "confidence_raw": confidence,
                "confidence": f"{confidence:.0%}",
                "score": f"{home_goals} - {away_goals}",
                "competition": match.get('competition'),
                "utcDate": match.get('utcDate')
            })
            logger.info(f"Prédiction générée pour {home_team_name} vs {away_team_name}")
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction pour {home_team_name} vs {away_team_name}: {e}", exc_info=True)


    top_10_predictions = all_predictions[:10]
    
    with open(DAILY_PREDICTIONS_PATH, 'w') as f:
        json.dump({"predictions": top_10_predictions}, f, indent=4)
    
    logger.info(f"{len(top_10_predictions)} prédictions sauvegardées.")

@app.on_event("startup")
def startup_event():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_daily_predictions, 'interval', days=1, misfire_grace_time=3600)
    scheduler.start()
    logger.info("Planificateur de tâches démarré.")
    # Exécuter une fois au démarrage pour avoir des données fraîches
    update_daily_predictions()

@app.get("/predictions")
def get_predictions():
    try:
        with open(DAILY_PREDICTIONS_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Le fichier de prédictions quotidiennes n'a pas encore été créé."}

@app.get("/teams")
def get_teams():
    """Retourne une liste de toutes les équipes uniques disponibles."""
    if historical_data is not None:
        home_teams = historical_data['home_team'].unique()
        away_teams = historical_data['away_team'].unique()
        all_teams = sorted(list(set(home_teams) | set(away_teams)))
        return {"teams": all_teams}
    return {"teams": []}

@app.post("/predict")
def get_prediction_for_teams(request: MatchPredictionRequest):
    """Prédit le résultat, les probabilités et le score d'un match."""
    if not all([outcome_model, home_model, away_model, model_columns, historical_data is not None, label_encoder is not None]):
        return {"error": "Modèles ou données non chargés."}

    try:
        outcome, probabilities, home_goals, away_goals = predict_outcome_and_score(
            request.home_team,
            request.away_team,
            historical_data,
            outcome_model,
            home_model,
            away_model,
            model_columns,
            label_encoder
        )
        
        return {
            "prediction": RESULT_MAPPING.get(outcome, "Inconnu"),
            "probabilities": {
                "away_win": probabilities.get('A', 0),
                "draw": probabilities.get('D', 0),
                "home_win": probabilities.get('H', 0)
            },
            "score": f"{home_goals} - {away_goals}"
        }
    except Exception as e:
        logger.error(f"Erreur dans /predict: {e}", exc_info=True)
        return {"error": f"Erreur lors de la prédiction: {e}"}

@app.post("/match-details")
def get_match_details(request: MatchPredictionRequest):
    """Retourne les statistiques de face-à-face et la forme récente pour deux équipes."""
    if historical_data is None:
        return {"error": "Données historiques non chargées."}

    home_team = request.home_team
    away_team = request.away_team

    # Head-to-Head
    h2h_games = historical_data[
        ((historical_data['home_team'] == home_team) & (historical_data['away_team'] == away_team)) |
        ((historical_data['home_team'] == away_team) & (historical_data['away_team'] == home_team))
    ].sort_values('date', ascending=False).head(5)

    # Recent Form
    home_form = historical_data[
        (historical_data['home_team'] == home_team) | (historical_data['away_team'] == home_team)
    ].sort_values('date', ascending=False).head(5)

    away_form = historical_data[
        (historical_data['home_team'] == away_team) | (historical_data['away_team'] == away_team)
    ].sort_values('date', ascending=False).head(5)

    return {
        "head_to_head": h2h_games.to_dict('records'),
        "home_team_form": home_form.to_dict('records'),
        "away_team_form": away_form.to_dict('records')
    }

@app.get("/team-logo/{team_name}")
def get_team_logo(team_name: str):
    """Récupère le logo d'une équipe depuis la carte de logos."""
    if logo_map is not None:
        return {"logoUrl": logo_map.get(team_name)}
    return {"logoUrl": None}
