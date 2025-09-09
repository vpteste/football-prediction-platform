import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
import joblib
from collections import deque

# --- 1. Chargement des données ---
def load_data(filepath="historical_data.csv"):
    """Charge et prépare les données initiales."""
    try:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except FileNotFoundError:
        print(f"Erreur: Le fichier {filepath} n'a pas été trouvé.")
        return None

# --- 2. Feature Engineering Super Avancé ---
def create_advanced_features(df):
    """Crée des caractéristiques basées sur la forme, les H2H et les différentiels."""
    print("Début du Feature Engineering Super Avancé...")
    
    df["result"] = df.apply(lambda row: "H" if row["home_goals"] > row["away_goals"] else ("A" if row["away_goals"] > row["home_goals"] else "D"), axis=1)

    team_stats = {}
    h2h_stats = {}
    
    # Initialisation des colonnes de features
    form_features = [
        'home_form_pts', 'home_form_gs', 'home_form_ga',
        'away_form_pts', 'away_form_gs', 'away_form_ga'
    ]
    h2h_features = ['h2h_home_wins', 'h2h_draws', 'h2h_away_wins']
    for col in form_features + h2h_features:
        df[col] = 0.0

    # Itération chronologique pour construire les features
    for index, row in df.iterrows():
        home_team, away_team = row['home_team'], row['away_team']

        # --- 2.1 Calcul de la forme (comme avant) ---
        if home_team not in team_stats: team_stats[home_team] = deque(maxlen=5)
        if away_team not in team_stats: team_stats[away_team] = deque(maxlen=5)

        if len(team_stats[home_team]) > 0:
            home_form = pd.DataFrame(list(team_stats[home_team]))
            df.loc[index, 'home_form_pts'] = home_form['pts'].mean()
            df.loc[index, 'home_form_gs'] = home_form['gs'].mean()
            df.loc[index, 'home_form_ga'] = home_form['ga'].mean()

        if len(team_stats[away_team]) > 0:
            away_form = pd.DataFrame(list(team_stats[away_team]))
            df.loc[index, 'away_form_pts'] = away_form['pts'].mean()
            df.loc[index, 'away_form_gs'] = away_form['gs'].mean()
            df.loc[index, 'away_form_ga'] = away_form['ga'].mean()

        # --- 2.2 Calcul du Head-to-Head (H2H) ---
        h2h_key = tuple(sorted((home_team, away_team)))
        if h2h_key not in h2h_stats: h2h_stats[h2h_key] = deque(maxlen=5)
        
        if len(h2h_stats[h2h_key]) > 0:
            h2h_results = list(h2h_stats[h2h_key])
            wins_for_key_0 = h2h_results.count('W')
            draws = h2h_results.count('D')
            
            if home_team == h2h_key[0]:
                df.loc[index, 'h2h_home_wins'] = wins_for_key_0
                df.loc[index, 'h2h_draws'] = draws
                df.loc[index, 'h2h_away_wins'] = len(h2h_results) - wins_for_key_0 - draws
            else: # home_team is h2h_key[1]
                df.loc[index, 'h2h_away_wins'] = wins_for_key_0
                df.loc[index, 'h2h_draws'] = draws
                df.loc[index, 'h2h_home_wins'] = len(h2h_results) - wins_for_key_0 - draws

        # --- 2.3 Mise à jour des stats pour le prochain match ---
        home_pts = 3 if row['result'] == 'H' else (1 if row['result'] == 'D' else 0)
        away_pts = 3 if row['result'] == 'A' else (1 if row['result'] == 'D' else 0)
        team_stats[home_team].append({'pts': home_pts, 'gs': row['home_goals'], 'ga': row['away_goals']})
        team_stats[away_team].append({'pts': away_pts, 'gs': row['away_goals'], 'ga': row['home_goals']})
        
        if row['result'] == 'D':
            h2h_stats[h2h_key].append('D')
        elif (row['result'] == 'H' and home_team == h2h_key[0]) or (row['result'] == 'A' and away_team == h2h_key[0]):
            h2h_stats[h2h_key].append('W') # Victoire pour la première équipe de la clé
        else:
            h2h_stats[h2h_key].append('L') # Défaite pour la première équipe de la clé

    # --- 2.4 Création des features différentielles ---
    df['home_form_gd'] = df['home_form_gs'] - df['home_form_ga']
    df['away_form_gd'] = df['away_form_gs'] - df['away_form_ga']
    df['diff_form_pts'] = df['home_form_pts'] - df['away_form_pts']
    df['diff_form_gs'] = df['home_form_gs'] - df['away_form_gs']
    df['diff_form_ga'] = df['home_form_ga'] - df['away_form_ga']
    df['diff_form_gd'] = df['home_form_gd'] - df['away_form_gd']
    
    # On retire les features H2H qui ne sont pas disponibles à la prédiction
    final_features = ['diff_form_pts', 'diff_form_gs', 'diff_form_ga', 'diff_form_gd']

    # Supprimer les matchs où il n'y avait pas assez d'historique (au moins un match de forme)
    df = df[df['home_form_pts'] > 0]
    df = df.dropna(subset=final_features)

    print("Feature Engineering terminé.")
    return df, final_features

# --- 3. Entraînement et Évaluation ---
def train_and_evaluate(df, feature_cols):
    """Divise les données, entraîne et évalue le modèle Gradient Boosting."""
    if df.empty:
        print("Le DataFrame est vide après le feature engineering, impossible d'entraîner.")
        return None

    X = df[feature_cols]
    y = df["result"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print(f"Taille de l'ensemble d'entraînement: {len(X_train)} matchs")
    print(f"Taille de l'ensemble de test: {len(X_test)} matchs")

    # Utilisation d'un modèle plus puissant
    model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
    
    print("\nEntraînement du modèle Gradient Boosting...")
    model.fit(X_train, y_train)
    print("Modèle entraîné.")

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nNOUVELLE Précision du modèle sur l'ensemble de test: {accuracy:.2%}")

    return model

# --- 4. Sauvegarde du modèle ---
def save_model(model, columns):
    """Sauvegarde le modèle et les colonnes de features."""
    try:
        joblib.dump(model, "prediction_model.joblib")
        joblib.dump(columns, "model_columns.joblib")
        print("\nModèle et colonnes sauvegardés avec succès.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du modèle: {e}")

# --- Script principal ---
if __name__ == "__main__":
    print("--- Début du processus d'entraînement avec Features Super Avancées ---")
    df = load_data()
    if df is not None:
        df_featured, feature_cols = create_advanced_features(df)
        trained_model = train_and_evaluate(df_featured, feature_cols)
        if trained_model:
            save_model(trained_model, feature_cols)
    print("\n--- Fin du processus d'entraînement ---")