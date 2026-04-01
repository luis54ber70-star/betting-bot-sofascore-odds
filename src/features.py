import pandas as pd

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Factor casa histórico por equipo
    if 'home_win' in df.columns and 'home_team' in df.columns:
        df["factor_casa"] = df.groupby("home_team")["home_win"].transform("mean").fillna(0.55)
    else:
        df["factor_casa"] = 1.0
    
    # Diferencia de xG
    if all(col in df.columns for col in ['xg_home', 'xg_away']):
        df["xg_diff"] = df["xg_home"] - df["xg_away"]
    else:
        df["xg_diff"] = 0.0
        print("⚠️ Columnas xg_home/xg_away no encontradas, usando 0.0")
    
    # ROI simple (rolling de últimos 10 partidos)
    if 'home_win' in df.columns:
        df["roi_home"] = (df["home_win"] * 1.0 - 1).rolling(window=10, min_periods=3).mean().fillna(0.0)
    else:
        df["roi_home"] = 0.0
    
    return df
