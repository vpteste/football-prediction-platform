import os
import requests
import pandas as pd
from dotenv import load_dotenv
import time

# --- Configuration ---
load_dotenv()
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

# On cible une seule compétition susceptible d'être dans le plan gratuit
COMPETITIONS = ['ELC'] 
SEASONS = [2022]
HEADERS = {"X-Auth-Token": API_KEY}
OUTPUT_FILE = "historical_data.csv"

def fetch_data():
    """Récupère les données pour une compétition et saison spécifiques."""
    if not API_KEY or API_KEY == "VOTRE_CLÉ_API_ICI":
        print("Erreur: Clé API pour football-data.org non trouvée.")
        return

    all_matches = []
    print(f"--- Récupération pour les compétitions: {COMPETITIONS} ---")
    for competition in COMPETITIONS:
        for season in SEASONS:
            print(f"Saison {season}...")
            api_url = f"https://api.football-data.org/v4/competitions/{competition}/matches"
            params = {"season": season, "status": "FINISHED"}
            try:
                response = requests.get(api_url, headers=HEADERS, params=params)
                response.raise_for_status()
                data = response.json()
                for match in data.get("matches", []):
                    all_matches.append({
                        "competition": competition,
                        "season": season,
                        "date": match["utcDate"],
                        "home_team": match["homeTeam"]["name"],
                        "away_team": match["awayTeam"]["name"],
                        "home_goals": match["score"]["fullTime"]["home"],
                        "away_goals": match["score"]["fullTime"]["away"],
                    })
                print(f"  -> {len(data.get('matches', []))} matchs récupérés.")
            except requests.exceptions.RequestException as e:
                print(f"  -> Erreur lors de la récupération: {e}")
                continue
            finally:
                time.sleep(6)

    if not all_matches:
        print("Aucune donnée n'a été récupérée. Arrêt.")
        return

    df = pd.DataFrame(all_matches)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDonnées sauvegardées avec succès dans {OUTPUT_FILE}")
    print(f"{len(df)} matchs au total ont été enregistrés.")

if __name__ == "__main__":
    fetch_data()