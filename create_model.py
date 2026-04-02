import joblib
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import os

# Crear carpeta models si no existe
os.makedirs("models", exist_ok=True)

# Crear modelo dummy funcional
model = RandomForestClassifier(n_estimators=50, random_state=42)
X_dummy = np.array([[0.5, 1.15, 0.0, 0, 0.3, 2.5]] * 100)
y_dummy = np.array([1] * 50 + [0] * 50)
model.fit(X_dummy, y_dummy)

joblib.dump(model, 'models/best_model.pkl')
print('✅ Modelo creado en models/best_model.pkl')
