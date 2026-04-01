import joblib
import pandas as pd
import os
from src.features import calculate_features

def kelly_criterion(prob: float, odds: float, bankroll: float = 1000, fraction: float = 0.5) -> float:
    """Calcula stake recomendado usando Half-Kelly Criterion"""
    if odds <= 1.0 or prob <= 0 or prob >= 1:
        return 0.0
    b = odds - 1
    q = 1 - prob
    kelly = (prob * b - q) / b
    if kelly <= 0:
        return 0.0
    stake = kelly * fraction * bankroll
    return round(max(stake, 0), 2)

def get_live_and_upcoming():
    """Versión estable temporal usando partidos dummy realistas"""
    print("🔍 Buscando partidos en vivo y próximos... (modo estable)")
    
    # Partidos dummy realistas de las 5 ligas top
    dummy_matches = [
        {
            "home_team": "Manchester City",
            "away_team": "Arsenal",
            "xg_home": 1.85,
            "xg_away": 1.25,
            "odds_home": 1.85,
            "status": "notstarted"
        },
        {
            "home_team": "Real Madrid",
            "away_team": "Barcelona",
            "xg_home": 1.95,
            "xg_away": 1.40,
            "odds_home": 2.10,
            "status": "notstarted"
        },
        {
            "home_team": "Bayern Munich",
            "away_team": "Borussia Dortmund",
            "xg_home": 2.10,
            "xg_away": 1.30,
            "odds_home": 1.72,
            "status": "inprogress"
        },
        {
            "home_team": "Liverpool",
            "away_team": "Chelsea",
            "xg_home": 1.75,
            "xg_away": 1.45,
            "odds_home": 2.05,
            "status": "notstarted"
        }
    ]
    
    print(f"✅ Usando {len(dummy_matches)} partidos dummy realistas")
    return dummy_matches

def generate_picks(min_value: float = 0.04, min_prob: float = 0.53, bankroll: float = 1000):
    model_path = "models/best_model.pkl"
    
    if not os.path.exists(model_path):
        return ["⚠️ Modelo no encontrado. Ejecuta el entrenamiento primero."]

    try:
        model = joblib.load(model_path)
        print(f"✅ Modelo cargado correctamente: {type(model).__name__}")

        live_matches = get_live_and_upcoming()

        picks = []
        features_list = ["xg_diff", "factor_casa", "roi_home"]

        for match in live_matches:
            try:
                row = pd.DataFrame([{
                    'xg_diff': match.get('xg_home', 0) - match.get('xg_away', 0),
                    'factor_casa': 1.0,
                    'roi_home': 0.0
                }])
                
                row = calculate_features(row)
                X = row[features_list]
                
                prob_home = model.predict_proba(X)[0][1]
                odds_home = match.get('odds_home', 2.0)
                
                value = prob_home - (1 / odds_home)
                
                if value > min_value and prob_home > min_prob:
                    stake = kelly_criterion(prob_home, odds_home, bankroll)
                    if stake >= 5.0:
                        status_emoji = "🔴 EN VIVO" if match.get("status") == "inprogress" else "⏳ PRÓXIMO"
                        pick_text = (
                            f"🚨 **VALUE BET DETECTADA** 🚨\n"
                            f"{status_emoji} {match['home_team']} vs {match['away_team']}\n"
                            f"Probabilidad modelo: **{prob_home:.1%}**\n"
                            f"Odds: **{odds_home:.2f}**\n"
                            f"Value: **+{value:.1%}**\n"
                            f"Stake recomendado (Half-Kelly): **${stake}**\n"
                            f"Bankroll: ${bankroll}"
                        )
                        picks.append(pick_text)
                        print(f"✅ Value encontrado: {match['home_team']} | Stake ${stake}")
            except Exception as e:
                print(f"Error procesando partido: {e}")
                continue

        if not picks:
            return ["✅ Análisis completado.\nNo se detectaron value bets con los umbrales actuales esta hora."]

        print(f"🎯 Generados {len(picks)} value picks")
        return picks

    except Exception as e:
        print(f"❌ Error en generate_picks: {e}")
        return ["❌ Error técnico al procesar los picks."]

if __name__ == "__main__":
    picks = generate_picks(bankroll=1000)
    for p in picks:
        print("\n" + p)
