import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
import xgboost as xgb
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, mean_absolute_error
import joblib
from collections import deque
import os

# --- Définir les chemins absolus ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORICAL_DATA_PATH = os.path.join(BASE_DIR, "historical_data_with_odds.csv") # Use the new data file
OUTCOME_MODEL_PATH = os.path.join(BASE_DIR, "outcome_model.joblib")
HOME_MODEL_PATH = os.path.join(BASE_DIR, "home_goals_model.joblib")
AWAY_MODEL_PATH = os.path.join(BASE_DIR, "away_goals_model.joblib")
COLUMNS_PATH = os.path.join(BASE_DIR, "model_columns.joblib")
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, "label_encoder.joblib")

# --- Paramètres de Feature Engineering ---
FORM_WINDOW_SIZE = 20

def load_data(filepath=HISTORICAL_DATA_PATH):
    """Charge et prépare les données initiales."""
    try:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except FileNotFoundError:
        print(f"Erreur: Le fichier {filepath} n'a pas été trouvé.")
        return None

def add_result_column(df):
    df["result"] = df.apply(lambda row: "H" if row["home_goals"] > row["away_goals"] else ("A" if row["away_goals"] > row["home_goals"] else "D"), axis=1)
    return df

def create_features(df):
    print("Début du Feature Engineering...")
    team_stats = {}
    form_features = ['home_form_pts', 'home_form_gs', 'home_form_ga', 'away_form_pts', 'away_form_gs', 'away_form_ga']
    for col in form_features:
        df[col] = 0.0

    for index, row in df.iterrows():
        home_team, away_team = row['home_team'], row['away_team']
        if home_team not in team_stats: team_stats[home_team] = deque(maxlen=FORM_WINDOW_SIZE)
        if away_team not in team_stats: team_stats[away_team] = deque(maxlen=FORM_WINDOW_SIZE)

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

        home_pts = 3 if row['result'] == 'H' else (1 if row['result'] == 'D' else 0)
        away_pts = 3 if row['result'] == 'A' else (1 if row['result'] == 'D' else 0)
        team_stats[home_team].append({'pts': home_pts, 'gs': row['home_goals'], 'ga': row['away_goals']})
        team_stats[away_team].append({'pts': away_pts, 'gs': row['away_goals'], 'ga': row['home_goals']})

    df['home_form_gd'] = df['home_form_gs'] - df['home_form_ga']
    df['away_form_gd'] = df['away_form_gs'] - df['away_form_ga']
    df['diff_form_pts'] = df['home_form_pts'] - df['away_form_pts']
    df['diff_form_gs'] = df['home_form_gs'] - df['away_form_gs']
    df['diff_form_ga'] = df['home_form_ga'] - df['away_form_ga']
    df['diff_form_gd'] = df['home_form_gd'] - df['away_form_gd']
    
    form_cols = ['home_form_pts', 'away_form_pts', 'home_form_gs', 'away_form_gs', 'home_form_ga', 'away_form_ga', 'home_form_gd', 'away_form_gd', 'diff_form_pts', 'diff_form_gs', 'diff_form_ga', 'diff_form_gd']
    df = df.dropna(subset=form_cols)

    print("Feature Engineering terminé.")
    return df, form_cols

def add_h2h_features(df):
    print("Ajout des caractéristiques Head-to-Head...")
    h2h_stats = {}
    h2h_cols = ['h2h_home_win_ratio', 'h2h_away_win_ratio', 'h2h_draw_ratio', 'h2h_avg_goals_for_home', 'h2h_avg_goals_for_away']
    for col in h2h_cols:
        df[col] = 0.0

    for index, row in df.iterrows():
        home_team, away_team = row['home_team'], row['away_team']
        matchup_key = tuple(sorted((home_team, away_team)))

        if matchup_key in h2h_stats:
            stats = h2h_stats[matchup_key]
            total_matches = stats['total_matches']
            if total_matches > 0:
                if home_team == matchup_key[0]:
                    df.loc[index, 'h2h_home_win_ratio'] = stats['team1_wins'] / total_matches
                    df.loc[index, 'h2h_away_win_ratio'] = stats['team2_wins'] / total_matches
                    df.loc[index, 'h2h_avg_goals_for_home'] = stats['team1_goals'] / total_matches
                    df.loc[index, 'h2h_avg_goals_for_away'] = stats['team2_goals'] / total_matches
                else:
                    df.loc[index, 'h2h_home_win_ratio'] = stats['team2_wins'] / total_matches
                    df.loc[index, 'h2h_away_win_ratio'] = stats['team1_wins'] / total_matches
                    df.loc[index, 'h2h_avg_goals_for_home'] = stats['team2_goals'] / total_matches
                    df.loc[index, 'h2h_avg_goals_for_away'] = stats['team1_goals'] / total_matches
                df.loc[index, 'h2h_draw_ratio'] = stats['draws'] / total_matches

        if matchup_key not in h2h_stats:
            h2h_stats[matchup_key] = {'total_matches': 0, 'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'team1_goals': 0, 'team2_goals': 0}
        
        stats = h2h_stats[matchup_key]
        stats['total_matches'] += 1
        if row['result'] == 'D': stats['draws'] += 1
        elif row['result'] == 'H':
            if home_team == matchup_key[0]: stats['team1_wins'] += 1
            else: stats['team2_wins'] += 1
        elif row['result'] == 'A':
            if away_team == matchup_key[0]: stats['team1_wins'] += 1
            else: stats['team2_wins'] += 1
        if home_team == matchup_key[0]:
            stats['team1_goals'] += row['home_goals']
            stats['team2_goals'] += row['away_goals']
        else:
            stats['team2_goals'] += row['home_goals']
            stats['team1_goals'] += row['away_goals']
    print("Caractéristiques Head-to-Head ajoutées.")
    return df, h2h_cols

def train_and_evaluate_classifier(df, feature_cols):
    print("\n--- Entraînement et optimisation du classifieur (XGBoost) ---")
    X = df[feature_cols]
    y_str = df["result"]
    le = LabelEncoder()
    y = le.fit_transform(y_str)
    joblib.dump(le, LABEL_ENCODER_PATH)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    param_grid = {'n_estimators': [100, 200], 'learning_rate': [0.05, 0.1], 'max_depth': [3, 5], 'subsample': [0.8, 1.0]}
    xgb_model = xgb.XGBClassifier(objective='multi:softmax', num_class=len(le.classes_), use_label_encoder=False, eval_metric='mlogloss', random_state=42)
    grid_search = GridSearchCV(estimator=xgb_model, param_grid=param_grid, cv=3, n_jobs=-1, verbose=2, scoring='accuracy')

    print("Début de la recherche des meilleurs hyperparamètres...")
    grid_search.fit(X_train, y_train)
    print(f"Meilleurs paramètres trouvés: {grid_search.best_params_}")

    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Précision du classifieur XGBoost optimisé: {accuracy:.2%}")
    return best_model

def train_and_evaluate_regressor(df, feature_cols, target_col):
    print(f"\n--- Entraînement du régresseur pour {target_col} ---")
    X = df[feature_cols]
    y = df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"MAE pour {target_col}: {mae:.2f} buts")
    return model

def save_models(outcome_model, home_model, away_model, columns):
    try:
        joblib.dump(outcome_model, OUTCOME_MODEL_PATH)
        joblib.dump(home_model, HOME_MODEL_PATH)
        joblib.dump(away_model, AWAY_MODEL_PATH)
        joblib.dump(columns, COLUMNS_PATH)
        print(f"\nModèles sauvegardés dans {BASE_DIR}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des modèles: {e}")

if __name__ == "__main__":
    print("--- Début du processus d'entraînement de tous les modèles ---")
    df = load_data()
    if df is not None:
        # 1. Filter for matches with odds data
        odds_cols = ['b365h', 'b365d', 'b365a', 'psh', 'psd', 'psa']
        df.dropna(subset=odds_cols, inplace=True)
        df.reset_index(drop=True, inplace=True)
        print(f"Found {len(df)} matches with complete odds data. Training on this subset.")

        # 2. Feature Engineering for odds
        print("Creating implied probability features from odds...")
        for bookmaker in ['b365', 'ps']:
            h_col, d_col, a_col = f'{bookmaker}h', f'{bookmaker}d', f'{bookmaker}a'
            prob_h_col, prob_d_col, prob_a_col = f'prob_{bookmaker}_h', f'prob_{bookmaker}_d', f'prob_{bookmaker}_a'
            
            df[prob_h_col] = 1 / df[h_col]
            df[prob_d_col] = 1 / df[d_col]
            df[prob_a_col] = 1 / df[a_col]
            
            total_prob = df[prob_h_col] + df[prob_d_col] + df[prob_a_col]
            df[prob_h_col] /= total_prob
            df[prob_d_col] /= total_prob
            df[prob_a_col] /= total_prob
        
        odds_feature_cols = odds_cols + [
            'prob_b365_h', 'prob_b365_d', 'prob_b365_a',
            'prob_ps_h', 'prob_ps_d', 'prob_ps_a'
        ]

        # 3. Standard Feature Engineering
        df = add_result_column(df)
        df, h2h_cols = add_h2h_features(df)
        df_featured, form_cols = create_features(df)
        
        # 4. Train Models
        feature_cols = form_cols + h2h_cols + odds_feature_cols
        feature_cols = list(dict.fromkeys(feature_cols))

        outcome_model = train_and_evaluate_classifier(df_featured, feature_cols)
        home_goals_model = train_and_evaluate_regressor(df_featured, feature_cols, 'home_goals')
        away_goals_model = train_and_evaluate_regressor(df_featured, feature_cols, 'away_goals')
        
        if all([outcome_model, home_goals_model, away_goals_model]):
            save_models(outcome_model, home_goals_model, away_goals_model, feature_cols)
            
    print("\n--- Fin du processus d'entraînement ---")
