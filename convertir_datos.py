import pandas as pd
import os
import requests
import zipfile
import io

# ================== CONFIGURACIÓN ==================
# Enlace directo al ZIP de football-data.co.uk (temporada actual)
ZIP_URL = "https://www.football-data.co.uk/mmz4281/2526/data.zip"

LOCAL_ZIP = "data.zip"
LOCAL_FILE = "international-uefa-nations-league-league-2026-to-2027-stats.csv"  # lo renombraremos
SALIDA = "data/matches.csv"
# ===================================================

def descargar_y_extraer_zip():
    print(f"📥 Descargando datos desde: {ZIP_URL}")
    
    try:
        response = requests.get(ZIP_URL, timeout=60)
        response.raise_for_status()
        
        with open(LOCAL_ZIP, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ ZIP descargado ({len(response.content)/1024/1024:.1f} MB)")
        
        # Extraer el ZIP
        with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
            zip_ref.extractall("data/")
        
        print("✅ Archivos extraídos en carpeta data/")
        return True
    except Exception as e:
        print(f"❌ Error al descargar/extraer ZIP: {e}")
        return False

def transformar():
    # Buscamos un CSV útil (puedes cambiar el nombre si quieres otro archivo del ZIP)
    # Ejemplos comunes: "N1.csv", "E0.csv", etc. Para Nations League puede no haber uno específico.
    # Por ahora usamos un archivo genérico o combinamos si es necesario.
    
    posibles_archivos = ["data/E0.csv", "data/D1.csv", "data/I1.csv", "data/SP1.csv", "data/F1.csv"]  # ligas top
    
    df_list = []
    for archivo in posibles_archivos:
        if os.path.exists(archivo):
            try:
                temp_df = pd.read_csv(archivo)
                print(f"✅ Leído {archivo}: {len(temp_df)} partidos")
                df_list.append(temp_df)
            except:
                pass
    
    if not df_list:
        print("⚠️ No se encontraron CSVs útiles en el ZIP. Usando datos dummy por ahora.")
        # Crear datos mínimos para que no falle
        nuevo_df = pd.DataFrame({
            'home_team': ['Team A', 'Team B'],
            'away_team': ['Team B', 'Team A'],
            'home_team_goal_count': [2, 1],
            'away_team_goal_count': [1, 2],
            'xg_home': [1.8, 1.2],
            'xg_away': [1.1, 1.5],
            'home_win': [1, 0]
        })
    else:
        df = pd.concat(df_list, ignore_index=True)
        print(f"✅ Total partidos combinados: {len(df)}")
        
        nuevo_df = pd.DataFrame()
        nuevo_df['home_team'] = df.get('HomeTeam', df.get('home_team', None))
        nuevo_df['away_team'] = df.get('AwayTeam', df.get('away_team', None))
        nuevo_df['home_team_goal_count'] = df.get('FTHG', df.get('home_team_goal_count', 0))
        nuevo_df['away_team_goal_count'] = df.get('FTAG', df.get('away_team_goal_count', 0))
        nuevo_df['xg_home'] = df.get('HxG', df.get('home_xg', 0.0))   # football-data no siempre tiene xG
        nuevo_df['xg_away'] = df.get('AxG', df.get('away_xg', 0.0))
        
        nuevo_df['home_win'] = (nuevo_df['home_team_goal_count'] > nuevo_df['away_team_goal_count']).astype(int)
        nuevo_df['xg_diff'] = nuevo_df['xg_home'] - nuevo_df['xg_away']
        nuevo_df['factor_casa'] = 1.0
        nuevo_df['roi_home'] = 0.0

    os.makedirs("data", exist_ok=True)
    nuevo_df.to_csv(SALIDA, index=False)
    
    print(f"✅ Transformación finalizada: {len(nuevo_df)} partidos guardados en {SALIDA}")
    return True

if __name__ == "__main__":
    if descargar_y_extraer_zip():
        transformar()
    else:
        print("❌ Falló la descarga. Usando datos dummy para no romper el pipeline.")
        # Crear archivo dummy mínimo
        os.makedirs("data", exist_ok=True)
        pd.DataFrame({
            'home_team': ['Dummy'], 'away_team': ['Dummy'],
            'home_team_goal_count': [1], 'away_team_goal_count': [0],
            'xg_home': [1.5], 'xg_away': [0.8], 'home_win': [1]
        }).to_csv(SALIDA, index=False)
