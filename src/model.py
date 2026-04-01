import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import joblib
import os
from src.features import calculate_features

def train_model():
    path = "data/matches.csv"
    
    # 1. VALIDACIÓN: ¿Existe el archivo y tiene datos?
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        print("⚠️ El archivo matches.csv no existe o está vacío. Saltando entrenamiento.")
        return None

    try:
        df = pd.read_csv(path)
        
        # 2. VALIDACIÓN: ¿Tiene el mínimo de filas para entrenar?
        if len(df) < 5: # Puedes subir este número cuando tengas más historial
            print(f"⚠️ Datos insuficientes ({len(df)} filas). Se necesitan al menos 5.")
            return None

        # Procesar características
        df = calculate_features(df)
        
        # Target: gana local (1) o no (0)
        # Asegúrate de que estas columnas existan en tu CSV
        features = ["xg_diff", "factor_casa", "roi_home"]
        X = df[features]
        y = df["home_win"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = xgb.XGBClassifier(
            n_estimators=200, 
            learning_rate=0.05, 
            max_depth=6,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        
        model.fit(X_train, y_train)
        
        # Crear carpeta models si no existe
        os.makedirs("models", exist_ok=True)
        
        # Guardar
        joblib.dump(model, "models/best_model.pkl")
        print("✅ Modelo re-entrenado y guardado exitosamente")
        return model

    except Exception as e:
        print(f"❌ Error durante el entrenamiento: {e}")
        return None

if __name__ == "__main__":
    train_model()
