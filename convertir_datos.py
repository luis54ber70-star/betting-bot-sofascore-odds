import pandas as pd
import os

def transformar():
    entrada = "international-uefa-nations-league-league-2026-to-2027-stats.csv"
    salida = "data/matches.csv"
    
    if not os.path.exists(entrada):
        print(f"❌ No se encuentra el archivo: {entrada}")
        return False

    try:
        df = pd.read_csv(entrada)
        print(f"✅ Archivo original leído: {len(df)} filas")
        print(f"Columnas originales: {list(df.columns)}")

        nuevo_df = pd.DataFrame()
        
        # Mapeo seguro de columnas (tu CSV puede tener nombres ligeramente diferentes)
        nuevo_df['home_team'] = df.get('home_team_name', df.get('team_a', df.get('home_team', None)))
        nuevo_df['away_team'] = df.get('away_team_name', df.get('team_b', df.get('away_team', None)))
        
        nuevo_df['home_team_goal_count'] = df.get('home_team_goal_count', df.get('team_a_goals', 0))
        nuevo_df['away_team_goal_count'] = df.get('away_team_goal_count', df.get('team_b_goals', 0))
        
        nuevo_df['xg_home'] = df.get('team_a_xg', df.get('xg_team_a', df.get('home_xg', 0.0)))
        nuevo_df['xg_away'] = df.get('team_b_xg', df.get('xg_team_b', df.get('away_xg', 0.0)))
        
        nuevo_df['home_win'] = (nuevo_df['home_team_goal_count'] > nuevo_df['away_team_goal_count']).astype(int)

        # Columnas requeridas por el modelo
        nuevo_df['xg_diff'] = nuevo_df['xg_home'] - nuevo_df['xg_away']
        nuevo_df['factor_casa'] = 1.0
        nuevo_df['roi_home'] = 0.0

        os.makedirs("data", exist_ok=True)
        nuevo_df.to_csv(salida, index=False)
        
        print(f"✅ Transformación exitosa: {len(nuevo_df)} partidos guardados en {salida}")
        print(f"Columnas finales: {list(nuevo_df.columns)}")
        print(nuevo_df.head())
        return True

    except Exception as e:
        print(f"❌ Error en transformar(): {e}")
        return False

if __name__ == "__main__":
    transformar()
