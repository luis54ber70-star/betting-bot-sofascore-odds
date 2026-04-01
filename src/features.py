import pandas as pd

def calculate_features(df_matches: pd.DataFrame):
    # Factor casa histórico (simple)
    df_matches["factor_casa"] = df_matches.groupby("home_team")["home_win"].transform("mean").fillna(0.55)
    
    # xG difference
    df_matches["xg_diff"] = df_matches["xg_home"] - df_matches["xg_away"]
    
    # ROI histórico simple (por equipo y mercado)
    df_matches["roi_home"] = (df_matches["home_win"] * 1.0 - 1).rolling(10).mean()
    
    return df_matches
