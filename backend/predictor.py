import pandas as pd
from collections import deque
import requests

def get_recent_stats(team_id, api_key, limit=5):
    """Récupère les statistiques de performance récentes pour une équipe."""
    headers = {'X-Auth-Token': api_key}
    url = f"http://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit={limit}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        matches = response.json().get('matches', [])
        
        if not matches:
            return {'recent_avg_gs': 0, 'recent_avg_ga': 0, 'recent_wins': 0, 'recent_draws': 0, 'recent_losses': 0}

        goals_scored = 0
        goals_conceded = 0
        wins = 0
        draws = 0
        losses = 0

        for match in matches:
            if match['score']['winner'] == 'DRAW':
                draws += 1
            elif (match['score']['winner'] == 'HOME_TEAM' and match['homeTeam']['id'] == team_id) or \
                 (match['score']['winner'] == 'AWAY_TEAM' and match['awayTeam']['id'] == team_id):
                wins += 1
            else:
                losses += 1

            if match['homeTeam']['id'] == team_id:
                goals_scored += match['score']['fullTime']['home']
                goals_conceded += match['score']['fullTime']['away']
            else:
                goals_scored += match['score']['fullTime']['away']
                goals_conceded += match['score']['fullTime']['home']
        
        num_matches = len(matches)
        return {
            'recent_avg_gs': goals_scored / num_matches,
            'recent_avg_ga': goals_conceded / num_matches,
            'recent_wins': wins,
            'recent_draws': draws,
            'recent_losses': losses
        }

    except requests.exceptions.RequestException as e:
        print(f"Erreur API lors de la récupération des stats pour l'équipe {team_id}: {e}")
        return None

def calculate_team_form(team_name, historical_data, last_n_matches=20):
    """Calcule la forme récente d'une équipe."""
    team_matches = historical_data[
        (historical_data['home_team'] == team_name) | 
        (historical_data['away_team'] == team_name)
    ].tail(last_n_matches)

    if team_matches.empty:
        return {'pts': 0, 'gs': 0, 'ga': 0, 'gd': 0}

    points = 0
    goals_scored = 0
    goals_conceded = 0

    for _, row in team_matches.iterrows():
        if row['home_team'] == team_name:
            points += 3 if row['home_goals'] > row['away_goals'] else (1 if row['home_goals'] == row['away_goals'] else 0)
            goals_scored += row['home_goals']
            goals_conceded += row['away_goals']
        else: # away_team
            points += 3 if row['away_goals'] > row['home_goals'] else (1 if row['away_goals'] == row['home_goals'] else 0)
            goals_scored += row['away_goals']
            goals_conceded += row['home_goals']
            
    avg_pts = points / len(team_matches)
    avg_gs = goals_scored / len(team_matches)
    avg_ga = goals_conceded / len(team_matches)

    return {
        'pts': avg_pts,
        'gs': avg_gs,
        'ga': avg_ga,
        'gd': avg_gs - avg_ga
    }

def get_h2h_stats_for_prediction(home_team, away_team, historical_data):
    """Calculates head-to-head stats for a new prediction."""
    h2h_matches = historical_data[
        ((historical_data['home_team'] == home_team) & (historical_data['away_team'] == away_team)) |
        ((historical_data['home_team'] == away_team) & (historical_data['away_team'] == home_team))
    ]

    if h2h_matches.empty:
        return {
            'h2h_home_win_ratio': 0, 'h2h_away_win_ratio': 0, 'h2h_draw_ratio': 0,
            'h2h_avg_goals_for_home': 0, 'h2h_avg_goals_for_away': 0
        }

    total_matches = len(h2h_matches)
    home_wins = 0
    away_wins = 0
    draws = 0
    home_goals = 0
    away_goals = 0

    for _, match in h2h_matches.iterrows():
        # Determine result from the perspective of the current home_team
        if match['result'] == 'D':
            draws += 1
        elif (match['result'] == 'H' and match['home_team'] == home_team) or \
             (match['result'] == 'A' and match['away_team'] == home_team):
            home_wins += 1
        else:
            away_wins += 1
        
        # Aggregate goals from the perspective of the current home_team
        if match['home_team'] == home_team:
            home_goals += match['home_goals']
            away_goals += match['away_goals']
        else: # away_team was the home team in the historical match
            home_goals += match['away_goals']
            away_goals += match['home_goals']

    return {
        'h2h_home_win_ratio': home_wins / total_matches,
        'h2h_away_win_ratio': away_wins / total_matches,
        'h2h_draw_ratio': draws / total_matches,
        'h2h_avg_goals_for_home': home_goals / total_matches,
        'h2h_avg_goals_for_away': away_goals / total_matches
    }

def predict_outcome_and_score(home_team_name, away_team_name, historical_data, outcome_model, home_model, away_model, model_columns, label_encoder):
    """Prédit le résultat, les probabilités et le score d'un match."""
    
    # Form features
    home_form = calculate_team_form(home_team_name, historical_data)
    away_form = calculate_team_form(away_team_name, historical_data)

    # H2H features
    h2h_stats = get_h2h_stats_for_prediction(home_team_name, away_team_name, historical_data)

    # Création des features pour le modèle
    input_data = {
        'home_form_pts': home_form['pts'],
        'away_form_pts': away_form['pts'],
        'home_form_gs': home_form['gs'],
        'away_form_gs': away_form['gs'],
        'home_form_ga': home_form['ga'],
        'away_form_ga': away_form['ga'],
        'home_form_gd': home_form['gd'],
        'away_form_gd': away_form['gd'],
        'diff_form_pts': home_form['pts'] - away_form['pts'],
        'diff_form_gs': home_form['gs'] - away_form['gs'],
        'diff_form_ga': home_form['ga'] - away_form['ga'],
        'diff_form_gd': home_form['gd'] - away_form['gd'],
        
        # Add H2H features
        'h2h_home_win_ratio': h2h_stats['h2h_home_win_ratio'],
        'h2h_away_win_ratio': h2h_stats['h2h_away_win_ratio'],
        'h2h_draw_ratio': h2h_stats['h2h_draw_ratio'],
        'h2h_avg_goals_for_home': h2h_stats['h2h_avg_goals_for_home'],
        'h2h_avg_goals_for_away': h2h_stats['h2h_avg_goals_for_away'],
    }
    
    # S'assurer que toutes les colonnes du modèle sont présentes
    for col in model_columns:
        if col not in input_data:
            input_data[col] = 0
            
    input_df = pd.DataFrame([input_data], columns=model_columns)

    # Prédiction du résultat (entier) et décodage
    outcome_prediction_encoded = outcome_model.predict(input_df)
    outcome_prediction = label_encoder.inverse_transform(outcome_prediction_encoded)[0]

    # Prédiction des probabilités et mapping avec les labels
    probabilities = outcome_model.predict_proba(input_df)[0]
    outcome_probabilities = {label: float(prob) for label, prob in zip(label_encoder.classes_, probabilities)}

    # Prédiction du score
    home_goals = round(home_model.predict(input_df)[0])
    away_goals = round(away_model.predict(input_df)[0])

    return outcome_prediction, outcome_probabilities, home_goals, away_goals
