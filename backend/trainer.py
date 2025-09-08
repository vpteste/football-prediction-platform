import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
from collections import deque

# --- 1. Chargement des données ---
def load_data(filepath="historical_data.csv"):
    """Charge et prépare les données initiales."""
    try:
        df = pd.read_csv(filepath)
        # Convertir la date en objet datetime et trier
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        return df
    except FileNotFoundError:
        print(f"Erreur: Le fichier {filepath} n'a pas été trouvé.")
        return None

# --- 2. Feature Engineering Avancé ---
def create_advanced_features(df):
    """Crée des caractéristiques basées sur la forme récente des équipes."""
    print("Début du Feature Engineering avancé...")
    
    # Calculer le résultat du match pour la variable cible
    df["result"] = df.apply(lambda row: "H" if row["home_goals"] > row["away_goals"] else ("A" if row["away_goals"] > row["home_goals"] else "D"), axis=1)

    # Dictionnaire pour garder en mémoire la forme récente de chaque équipe
    team_stats = {}
    
    # Nouvelles colonnes pour les features, initialisées à 0
    new_features = [
        'home_form_pts', 'home_form_gs', 'home_form_ga', 'home_form_gd',
        'away_form_pts', 'away_form_gs', 'away_form_ga', 'away_form_gd'
    ]
    for col in new_features:
        df[col] = 0.0

    # Itérer sur chaque match dans l'ordre chronologique
    for index, row in df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']

        # Initialiser les stats pour les nouvelles équipes
        if home_team not in team_stats: team_stats[home_team] = deque(maxlen=5)
        if away_team not in team_stats: team_stats[away_team] = deque(maxlen=5)

        # Assigner les stats actuelles (avant ce match) au match courant
        if len(team_stats[home_team]) > 0:
            home_stats = pd.DataFrame(list(team_stats[home_team]))
            df.loc[index, 'home_form_pts'] = home_stats['pts'].mean()
            df.loc[index, 'home_form_gs'] = home_stats['gs'].mean()
            df.loc[index, 'home_form_ga'] = home_stats['ga'].mean()
            df.loc[index, 'home_form_gd'] = home_stats['gd'].mean()

        if len(team_stats[away_team]) > 0:
            away_stats = pd.DataFrame(list(team_stats[away_team]))
            df.loc[index, 'away_form_pts'] = away_stats['pts'].mean()
            df.loc[index, 'away_form_gs'] = away_stats['gs'].mean()
            df.loc[index, 'away_form_ga'] = away_stats['ga'].mean()
            df.loc[index, 'away_form_gd'] = away_stats['gd'].mean()

        # Mettre à jour les stats avec le résultat de ce match
        home_pts = 3 if row['result'] == 'H' else (1 if row['result'] == 'D' else 0)
        away_pts = 3 if row['result'] == 'A' else (1 if row['result'] == 'D' else 0)
        team_stats[home_team].append({'pts': home_pts, 'gs': row['home_goals'], 'ga': row['away_goals'], 'gd': row['home_goals'] - row['away_goals']})
        team_stats[away_team].append({'pts': away_pts, 'gs': row['away_goals'], 'ga': row['home_goals'], 'gd': row['away_goals'] - row['home_goals']})

    # Supprimer les matchs où il n'y avait pas assez d'historique
    df = df[df['home_form_pts'].notna() & df['away_form_pts'].notna()] # En pratique, on a initialisé à 0 donc pas de NA
    df = df.dropna(subset=new_features)

    print("Feature Engineering terminé.")
    return df, new_features

# --- 3. Entraînement et Évaluation ---
def train_and_evaluate(df, feature_cols):
    """Divise les données, entraîne et évalue le modèle."""
    if df.empty:
        print("Le DataFrame est vide après le feature engineering, impossible d'entraîner.")
        return None

    X = df[feature_cols]
    y = df["result"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print(f"Taille de l'ensemble d'entraînement: {len(X_train)} matchs")
    print(f"Taille de l'ensemble de test: {len(X_test)} matchs")

    model = LogisticRegression(max_iter=1000)
    print("\nEntraînement du modèle...")
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
    print("--- Début du processus d'entraînement avec Features Avancées ---")
    df = load_data()
    if df is not None:
        df_featured, feature_cols = create_advanced_features(df)
        trained_model = train_and_evaluate(df_featured, feature_cols)
        if trained_model:
            # Si l'entraînement a réussi, on sauvegarde le nouveau modèle
            save_model(trained_model, feature_cols)
    print("\n--- Fin du processus d'entraînement ---")