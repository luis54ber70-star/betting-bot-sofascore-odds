import pandas as pd
import numpy as np

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if 'xg_home' in df.columns and 'xg_away' in df.columns:
        df['xg_diff'] = df['xg_home'] - df['xg_away']
        df['xg_ratio'] = df['xg_home'] / (df['xg_away'] + 0.001)
        df['xg_total'] = df['xg_home'] + df['xg_away']
    else:
        df['xg_diff'] = 0.0
        df['xg_ratio'] = 1.0
        df['xg_total'] = 2.2

    df['goal_diff'] = df.get('home_team_goal_count', 0) - df.get('away_team_goal_count', 0)
    df['factor_casa'] = 1.0
    df['roi_home'] = 0.0
    df['is_strong_league'] = 1

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df
