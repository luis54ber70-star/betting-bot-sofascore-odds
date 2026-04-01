import pandas as pd
import os
from src.sofascore_scraper import get_live_and_upcoming, get_match_statistics
from datetime import datetime

# 1. Obtener datos
df = get_live_and_upcoming()

# 2. VALIDACIÓN CRÍTICA: Si no hay datos, no intentes guardar nada
if df is None or df.empty:
    print("⚠️ No se encontraron partidos nuevos para recolectar.")
else:
    # 3. Solo guarda si el archivo NO existe o si tiene datos reales
    file_path = "data/matches.csv"
    
    # Nos aseguramos de que la carpeta exista
    os.makedirs("data", exist_ok=True)
    
    # Escribir al CSV
    # Si el archivo no existe, escribe cabeceras. Si existe, solo añade datos (mode='a')
    file_exists = os.path.isfile(file_path)
    
    df.to_csv(file_path, mode="a", header=not file_exists, index=False)
    print(f"✅ Datos actualizados: {len(df)} partidos añadidos a {file_path}")
