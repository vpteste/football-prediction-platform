import os
import requests
import json
import time
import pandas as pd
from dotenv import load_dotenv
from collections import deque

# Charger les variables d'environnement
load_dotenv()
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
HEADERS = {"X-Auth-Token": API_KEY}

# Configuration
COMPETITIONS = ['WC', 'CL', 'BL1', 'DED', 'BSA', 'PD', 'FL1', 'ELC', 'PPL', 'EC', 'SA', 'PL']
OUTPUT_FILE = "feature_cache.json"

def get_all_teams():
    """Récupère toutes les équipes des compétitions spécifiées."""
    all_teams = {}
    print("Récupération de la liste des équipes...")
    for competition_code in COMPETITIONS:
        try:
            url = f"https://api.football-data.org/v4/competitions/{competition_code}/teams"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            teams_data = response.json().get('teams', [])
            for team in teams_data:
                all_teams[team['id']] = team['name']
            print(f"  -> {len(teams_data)} équipes trouvées pour {competition_code}.")
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération des équipes pour {competition_code}: {e}")
        finally:
            time.sleep(6) # Respecter la limite de l'API
    return all_teams

def calculate_team_form(teams):
    """Calcule la forme récente pour chaque équipe et la sauvegarde."""
    team_form_cache = {}
    total_teams = len(teams)
    print(f"\nCalcul de la forme pour {total_teams} équipes. Cela peut prendre du temps...")

    for i, (team_id, team_name) in enumerate(teams.items()):
        print(f"[{i+1}/{total_teams}] Calcul pour: {team_name}")
        try:
            url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            matches = response.json().get('matches', [])

            if not matches:
                continue

            stats = []
            for match in matches:
                is_home_team = match['homeTeam']['id'] == team_id
                result = match['score']['winner']
                
                if (is_home_team and result == 'HOME_TEAM') or (not is_home_team and result == 'AWAY_TEAM'):
                    pts = 3
                elif result == 'DRAW':
                    pts = 1
                else:
                    pts = 0

                gs = match['score']['fullTime']['home'] if is_home_team else match['score']['fullTime']['away']
                ga = match['score']['fullTime']['away'] if is_home_team else match['score']['fullTime']['home']
                
                stats.append({'pts': pts, 'gs': gs, 'ga': ga, 'gd': gs - ga})
            
            form_stats = pd.DataFrame(stats).mean().to_dict()
            team_form_cache[team_name] = form_stats

        except requests.RequestException as e:
            print(f"  -> Erreur pour {team_name}: {e}")
        finally:
            time.sleep(6) # Respecter la limite de l'API

    # Sauvegarder le cache
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(team_form_cache, f, indent=4)
    
    print(f"\nCache de forme sauvegardé avec succès dans {OUTPUT_FILE}")

if __name__ == "__main__":
    if not API_KEY or API_KEY == "VOTRE_CLÉ_API_ICI":
        print("Erreur: Clé API non trouvée. Vérifiez votre fichier .env")
    else:
        teams_dict = get_all_teams()
        if teams_dict:
            calculate_team_form(teams_dict)
