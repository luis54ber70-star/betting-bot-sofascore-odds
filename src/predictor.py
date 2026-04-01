import joblib
import pandas as pd
import os
from src.features import calculate_features

def kelly_criterion(prob: float, odds: float, bankroll: float = 1000, fraction: float = 0.5) -> float:
    if odds <= 1.0 or prob <= 0 or prob >= 1:
        return 0.0
    b = odds - 1
    q = 1 - prob
    kelly = (prob * b - q) / b
    if kelly <= 0:
        return 0.0
    stake = kelly * fraction * bankroll
    return round(max(stake, 0), 2)

def generate_picks(min_value: float = 0.04, min_prob: float = 0.53, bankroll: float = 1000):
    model_path = "models/best_model.pkl"
    
    if not os.path.exists(model_path):
        return ["⚠️ Modelo no disponible."]

    model = joblib.load(model_path)
    print(f"✅ Modelo cargado: {type(model).__name__}")

    # Placeholder - Cambia esto cuando tengas odds_fetcher listo
    live_matches = []  

    if not live_matches:
        return ["✅ Bot activo cada hora.\nNo hay partidos con odds disponibles en este momento."]

    picks = []
    features = ["xg_diff", "factor_casa", "roi_home"]

    for match in live_matches[:8]:
        try:
            row = pd.DataFrame([{
                'xg_diff': match.get('xg_home', 0) - match.get('xg_away', 0),
                'factor_casa': 1.0,
                'roi_home': 0.0
            }])
            row = calculate_features(row)
            X = row[features]
            
            prob_home = model.predict_proba(X)[0][1]
            odds_home = match.get('odds_home') or 2.0
            
            value = prob_home - (1 / odds_home)
            
            if value > min_value and prob_home > min_prob:
                stake = kelly_criterion(prob_home, odds_home, bankroll)
                if stake >= 5:
                    pick_text = (
                        f"🚨 **VALUE BET** 🚨\n"
                        f"{match.get('home_team')} vs {match.get('away_team')}\n"
                        f"Prob: {prob_home:.1%} | Odds: {odds_home:.2f}\n"
                        f"Value: +{value:.1%} | Stake: ${stake}"
                    )
                    picks.append(pick_text)
        except:
            continue

    return picks if picks else ["✅ Sin value bets esta hora."]

if __name__ == "__main__":
    generate_picks()
