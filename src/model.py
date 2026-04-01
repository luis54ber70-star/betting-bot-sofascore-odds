import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import joblib
from src.features import calculate_features

def train_model():
    df = pd.read_csv("data/matches.csv")
    df = calculate_features(df)
    
    # Target: gana local (1) o no (0) - puedes cambiar a over2.5 etc.
    X = df[["xg_diff", "factor_casa", "roi_home"]]
    y = df["home_win"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBClassifier(n_estimators=200, learning_rate=0.05, max_depth=6)
    model.fit(X_train, y_train)
    
    # Guardar
    joblib.dump(model, "models/best_model.pkl")
    print("✅ Modelo re-entrenado y guardado")
    return model
