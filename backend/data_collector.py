import os
import requests
import pandas as pd
from dotenv import load_dotenv
import time

# Charger les variables d'environnement
load_dotenv()
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

# Configuration
COMPETITIONS = ['WC', 'CL', 'BL1', 'DED', 'BSA', 'PD', 'FL1', 'ELC', 'PPL', 'EC', 'SA', 'PL']
SEASONS = [2022, 2023] # Saisons à récupérer
HEADERS = {"X-Auth-Token": API_KEY}
OUTPUT_FILE = "historical_data.csv"

def fetch_data():
    """Récupère les données des saisons et compétitions spécifiées et les sauvegarde dans un fichier CSV."""
    if not API_KEY or API_KEY == "VOTRE_CLÉ_API_ICI":
        print("Erreur: Clé API non trouvée. Vérifiez votre fichier .env")
        return

    all_matches = []

    for competition in COMPETITIONS:
        print(f"\n--- Récupération pour la compétition: {competition} ---")
        for season in SEASONS:
            print(f"Saison {season}...")
            api_url = f"https://api.football-data.org/v4/competitions/{competition}/matches"
            params = {"season": season, "status": "FINISHED"}
            
            try:
                response = requests.get(api_url, headers=HEADERS, params=params)
                response.raise_for_status()
                data = response.json()

                for match in data.get("matches", []):
                    match_data = {
                        "competition": competition,
                        "season": season,
                        "date": match["utcDate"],
                        "home_team": match["homeTeam"]["name"],
                        "away_team": match["awayTeam"]["name"],
                        "home_goals": match["score"]["fullTime"]["home"],
                        "away_goals": match["score"]["fullTime"]["away"],
                    }
                    all_matches.append(match_data)
                
                print(f"  -> {len(data.get('matches', []))} matchs récupérés pour la saison {season}.")

            except requests.exceptions.RequestException as e:
                print(f"  -> Erreur lors de la récupération de la saison {season} pour {competition}: {e}")
                continue
            finally:
                # Pause de 6 secondes pour respecter la limite de 10 appels/minute de l'API
                time.sleep(6)

    if not all_matches:
        print("Aucune donnée n'a été récupérée. Arrêt du script.")
        return

    df = pd.DataFrame(all_matches)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDonnées sauvegardées avec succès dans {OUTPUT_FILE}")
    print(f"{len(df)} matchs au total ont été enregistrés.")

if __name__ == "__main__":
    fetch_data()
