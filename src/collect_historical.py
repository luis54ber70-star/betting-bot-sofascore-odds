import pandas as pd
from src.sofascore_scraper import get_live_and_upcoming, get_match_statistics
from datetime import datetime, timedelta

# Aquí recolecta datos de los últimos 30 días o usa un loop por ligas
# Por simplicidad guardamos en CSV (puedes expandir)

df = get_live_and_upcoming()
# Añade stats y resultados (en histórico ya sabes el resultado)
# ... (expande según necesites)
df.to_csv("data/matches.csv", mode="a", header=not pd.io.common.file_exists("data/matches.csv"), index=False)
print("Datos históricos actualizados")
