import pandas as pd
import os
import requests
import zipfile

ZIP_URL = "https://www.football-data.co.uk/mmz4281/2526/data.zip"
SALIDA = "data/matches.csv"
LIGAS_TOP = ["E0.csv", "SP1.csv", "D1.csv", "I1.csv", "F1.csv"]

def descargar_y_extraer_zip():
    print("📥 Descargando datos de las 5 mejores ligas...")
    try:
        response = requests.get(ZIP_URL, timeout=60)
        response.raise_for_status()
        with open("data.zip", 'wb') as f:
            f.write(response.content)
        with zipfile.ZipFile("data.zip", 'r') as zip_ref:
            zip_ref.extractall("data/")
        print("✅ Datos descargados y extraídos")
        return True
    except Exception as e:
        print(f"❌ Error descarga: {e}")
        return False

def transformar():
    df_list = []
    for archivo in LIGAS_TOP:
        path = f"data/{archivo}"
        if os.path.exists(path):
            temp_df = pd.read_csv(path)
            print(f"✅ {archivo}: {len(temp_df)} partidos")
            df_list.append(temp_df)

    df = pd.concat(df_list, ignore_index=True)
    print(f"✅ Total partidos Top 5: {len(df)}")

    nuevo_df = pd.DataFrame()
    nuevo_df['home_team'] = df.get('HomeTeam')
    nuevo_df['away_team'] = df.get('AwayTeam')
    nuevo_df['home_team_goal_count'] = df.get('FTHG', 0)
    nuevo_df['away_team_goal_count'] = df.get('FTAG', 0)
    nuevo_df['xg_home'] = df.get('HxG', 0.0)
    nuevo_df['xg_away'] = df.get('AxG', 0.0)

    nuevo_df['home_win'] = (nuevo_df['home_team_goal_count'] > nuevo_df['away_team_goal_count']).astype(int)
    nuevo_df['xg_diff'] = nuevo_df['xg_home'] - nuevo_df['xg_away']
    nuevo_df['factor_casa'] = 1.0
    nuevo_df['roi_home'] = 0.0

    os.makedirs("data", exist_ok=True)
    nuevo_df.to_csv(SALIDA, index=False)
    print(f"✅ matches.csv generado con {len(nuevo_df)} partidos")
    return True

if __name__ == "__main__":
    descargar_y_extraer_zip()
    transformar()
