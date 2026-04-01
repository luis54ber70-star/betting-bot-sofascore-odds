import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import joblib
import os
from src.features import calculate_features

def train_model():
    path = "data/matches.csv"
    
    # Validaciones fuertes
    if not os.path.exists(path):
        print(f"⚠️ El archivo {path} no existe.")
        return None
    if os.stat(path).st_size == 0:
        print("⚠️ El archivo matches.csv está vacío.")
        return None

    try:
        df = pd.read_csv(path)
        print(f"✅ Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas")
        
        if len(df) < 10:
            print(f"⚠️ Datos insuficientes ({len(df)} filas). Se necesitan al menos 10.")
            return None

        # Calcular características
        df = calculate_features(df)
        
        # Features y target
        features = ["xg_diff", "factor_casa", "roi_home"]
        X = df[features]
        y = df["home_win"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = xgb.XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            eval_metric='logloss',
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Guardar modelo
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/best_model.pkl")
        
        print("✅ Modelo entrenado y guardado correctamente en models/best_model.pkl")
        print(f"Precisión aproximada en test: {model.score(X_test, y_test):.4f}")
        return model

    except Exception as e:
        print(f"❌ Error durante el entrenamiento: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    train_model()
