import pandas as pd
import os
import requests
import zipfile

# ================== CONFIGURACIÓN ==================
ZIP_URL = "https://www.football-data.co.uk/mmz4281/2526/data.zip"
LOCAL_ZIP = "data.zip"
SALIDA = "data/matches.csv"

# Ligas Top 5 del mundo para value betting (2025/2026)
LIGAS_TOP = ["E0.csv", "SP1.csv", "D1.csv", "I1.csv", "F1.csv"]  # Premier, LaLiga, Bundesliga, Serie A, Ligue 1
# ===================================================

def descargar_y_extraer_zip():
    print(f"📥 Descargando datos históricos desde football-data.co.uk...")
    try:
        response = requests.get(ZIP_URL, timeout=60)
        response.raise_for_status()
        
        with open(LOCAL_ZIP, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ ZIP descargado ({len(response.content)/1024/1024:.1f} MB)")
        
        with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
            zip_ref.extractall("data/")
        
        print("✅ Archivos extraídos correctamente")
        return True
    except Exception as e:
        print(f"❌ Error descargando ZIP: {e}")
        return False

def transformar():
    df_list = []
    for archivo in LIGAS_TOP:
        path = f"data/{archivo}"
        if os.path.exists(path):
            try:
                temp_df = pd.read_csv(path)
                print(f"✅ Leído {archivo}: {len(temp_df)} partidos")
                df_list.append(temp_df)
            except Exception as e:
                print(f"⚠️ Error leyendo {archivo}: {e}")
    
    if not df_list:
        print("⚠️ No se encontraron ligas top. Creando datos mínimos...")
        nuevo_df = pd.DataFrame({
            'home_team': ['Dummy Home'], 'away_team': ['Dummy Away'],
            'home_team_goal_count': [2], 'away_team_goal_count': [1],
            'xg_home': [1.8], 'xg_away': [1.2], 'home_win': [1]
        })
    else:
        df = pd.concat(df_list, ignore_index=True)
        print(f"✅ Total partidos Top 5 ligas: {len(df)}")
        
        nuevo_df = pd.DataFrame()
        nuevo_df['home_team'] = df.get('HomeTeam')
        nuevo_df['away_team'] = df.get('AwayTeam')
        nuevo_df['home_team_goal_count'] = df.get('FTHG', 0)
        nuevo_df['away_team_goal_count'] = df.get('FTAG', 0)
        nuevo_df['xg_home'] = df.get('HxG', df.get('home_xg', 0.0))
        nuevo_df['xg_away'] = df.get('AxG', df.get('away_xg', 0.0))
        
        nuevo_df['home_win'] = (nuevo_df['home_team_goal_count'] > nuevo_df['away_team_goal_count']).astype(int)
        nuevo_df['xg_diff'] = nuevo_df['xg_home'] - nuevo_df['xg_away']
        nuevo_df['factor_casa'] = 1.0
        nuevo_df['roi_home'] = 0.0

    os.makedirs("data", exist_ok=True)
    nuevo_df.to_csv(SALIDA, index=False)
    
    print(f"✅ matches.csv generado con {len(nuevo_df)} partidos de las 5 mejores ligas")
    return True

if __name__ == "__main__":
    if descargar_y_extraer_zip():
        transformar()
    else:
        print("❌ Falló la descarga. Creando archivo dummy mínimo...")
        os.makedirs("data", exist_ok=True)
        pd.DataFrame({
            'home_team': ['Team A'], 'away_team': ['Team B'],
            'home_team_goal_count': [2], 'away_team_goal_count': [1],
            'xg_home': [1.7], 'xg_away': [1.1], 'home_win': [1]
        }).to_csv(SALIDA, index=False)
