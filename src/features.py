import pandas as pd
import numpy as np
from datetime import datetime

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula features para el modelo XGBoost.
    Funciona tanto para datos históricos como para partidos en vivo (con valores placeholder).
    """
    if df.empty:
        return df

    df = df.copy()

    # Features básicas de xG (si existen)
    if 'xg_home' in df.columns and 'xg_away' in df.columns:
        df['xg_diff'] = df['xg_home'] - df['xg_away']
        df['xg_ratio'] = df['xg_home'] / (df['xg_away'] + 0.01)  # evitar división por cero
    else:
        df['xg_diff'] = 0.0
        df['xg_ratio'] = 1.0

    # Goals difference (útil en histórico)
    if 'home_team_goal_count' in df.columns and 'away_team_goal_count' in df.columns:
        df['goal_diff'] = df['home_team_goal_count'] - df['away_team_goal_count']
    else:
        df['goal_diff'] = 0

    # Factor casa (mejorado: 1.0 para local, pero se puede enriquecer después)
    df['factor_casa'] = 1.0

    # ROI home (placeholder por ahora - puedes mejorarlo con datos históricos de odds)
    df['roi_home'] = 0.0

    # Features adicionales recomendadas para reducir ruido
    df['is_strong_league'] = 1  # placeholder: pon 1 para ligas top (EPL, LaLiga, etc.)

    # Encoding simple de equipos (label encoding básico)
    if 'home_team' in df.columns:
        # Creamos un código numérico combinado para home + away
        df['team_combo'] = df['home_team'].astype(str) + "_" + df['away_team'].astype(str)
        # Para live, si no hay muchos equipos, usamos frecuencia o valor por defecto
        if len(df) > 50:  # solo en histórico grande
            team_freq = pd.concat([df['home_team'], df['away_team']]).value_counts()
            df['home_strength'] = df['home_team'].map(team_freq).fillna(10)
            df['away_strength'] = df['away_team'].map(team_freq).fillna(10)
        else:
            df['home_strength'] = 20.0
            df['away_strength'] = 20.0

    # Rellenar NaNs
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    print(f"Features calculadas. Columnas finales: {df.columns.tolist()}")
    return df
