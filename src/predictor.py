import joblib
import pandas as pd
from src.sofascore_scraper import get_match_statistics
from src.odds_fetcher import get_odds
from src.features import calculate_features

def generate_picks():
    model = joblib.load("models/best_model.pkl")
    live_matches = get_live_and_upcoming()  # o upcoming según necesites
    
    picks = []
    for _, match in live_matches.iterrows():
        stats = get_match_statistics(match["match_id"])
        if not stats:
            continue
            
        odds_df = get_odds()  # filtra por equipo si quieres
        # Ejemplo simple: buscar odd del local
        home_odd = 2.0  # placeholder - busca en odds_df
        
        # Features
        features = pd.DataFrame([{
            "xg_diff": stats["xg_home"] - stats["xg_away"],
            "factor_casa": 0.58,  # placeholder - calcula real
            "roi_home": 0.12
        }])
        
        prob = model.predict_proba(features)[0][1]
        implied_prob = 1 / home_odd
        
        if prob > implied_prob + 0.10:  # edge > 10%
            picks.append(f"✅ PICK: {match['home_team']} gana @ {home_odd} | Prob real: {prob:.1%} | Edge: {prob - implied_prob:.1%}")
    
    return picks
