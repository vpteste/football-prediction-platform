import pandas as pd
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
HISTORICAL_DATA_PATH = os.path.join(os.path.dirname(__file__), "historical_data.csv")
TEAM_ID_MAP_PATH = os.path.join(os.path.dirname(__file__), "team_id_map.json")

def create_team_id_map():
    """
    Crée une carte entre les noms d'équipe de notre dataset et leurs IDs de l'API football-data.org.
    """
    if not FOOTBALL_DATA_API_KEY:
        print("Erreur: La clé API FOOTBALL_DATA_API_KEY n'est pas définie.")
        return

    try:
        df = pd.read_csv(HISTORICAL_DATA_PATH)
        home_teams = df['home_team'].unique()
        away_teams = df['away_team'].unique()
        all_teams = sorted(list(set(home_teams) | set(away_teams)))
        print(f"{len(all_teams)} équipes uniques trouvées dans le dataset.")
    except FileNotFoundError:
        print(f"Erreur: Le fichier {HISTORICAL_DATA_PATH} est introuvable.")
        return

    team_id_map = {}
    headers = {'X-Auth-Token': FOOTBALL_DATA_API_KEY}
    competitions_url = "http://api.football-data.org/v4/competitions"

    try:
        response = requests.get(competitions_url, headers=headers)
        response.raise_for_status()
        competitions = response.json().get('competitions', [])
        print(f"Scan de {len(competitions)} compétitions pour les IDs d'équipes...")

        for comp in competitions:
            teams_url = f"http://api.football-data.org/v4/competitions/{comp['id']}/teams"
            try:
                teams_response = requests.get(teams_url, headers=headers)
                if teams_response.status_code == 200:
                    teams_data = teams_response.json().get('teams', [])
                    for team_api in teams_data:
                        # Simple matching, can be improved with fuzzy matching
                        for team_local in all_teams:
                            if team_local.lower() == team_api['name'].lower() or team_local.lower() == team_api['shortName'].lower():
                                if team_local not in team_id_map:
                                    team_id_map[team_local] = team_api['id']
                                    print(f"  [+] Trouvé: {team_local} -> {team_api['id']}")
            except requests.exceptions.RequestException as e:
                print(f"  Avertissement: Impossible de récupérer les équipes pour la compétition {comp['id']}: {e}")
                continue

        with open(TEAM_ID_MAP_PATH, 'w') as f:
            json.dump(team_id_map, f, indent=4)
        
        print(f"\nCarte des IDs d'équipes créée avec succès ! {len(team_id_map)}/{len(all_teams)} IDs trouvés.")
        print(f"Carte sauvegardée dans {TEAM_ID_MAP_PATH}")

    except requests.exceptions.RequestException as e:
        print(f"Erreur API: {e}")

if __name__ == "__main__":
    create_team_id_map()
