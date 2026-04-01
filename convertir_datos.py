import pandas as pd
import os

def transformar():
    # Nombre exacto del archivo que tienes en tu repo
    entrada = "international-uefa-nations-league-league-2026-to-2027-stats.csv"
    salida = "data/matches.csv"
    
    if not os.path.exists(entrada):
        print(f"❌ No se encuentra el archivo: {entrada}")
        return

    try:
        df = pd.read_csv(entrada)
        nuevo_df = pd.DataFrame()
        
        # Extraemos las columnas necesarias para tu modelo
        nuevo_df['xg_diff'] = df['team_a_xg'] - df['team_b_xg']
        nuevo_df['factor_casa'] = 1
        nuevo_df['roi_home'] = 0.0
        nuevo_df['home_win'] = (df['home_team_goal_count'] > df['away_team_goal_count']).astype(int)

        os.makedirs("data", exist_ok=True)
        nuevo_df.to_csv(salida, index=False)
        print(f"✅ Éxito: {len(nuevo_df)} partidos convertidos en {salida}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    transformar()
