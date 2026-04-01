import joblib
import pandas as pd
import os
from src.features import calculate_features

def kelly_criterion(prob: float, odds: float, bankroll: float = 1000, fraction: float = 0.5) -> float:
    """Kelly Criterion fraccional (Half-Kelly recomendado para menor riesgo)"""
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
        return ["⚠️ Modelo no encontrado. Ejecuta Retrain Model primero."]

    try:
        model = joblib.load(model_path)
        print(f"✅ Modelo cargado correctamente: {type(model).__name__}")

        # ←←← AQUÍ VA TU FUNCIÓN REAL DE ODDS (cuando la tengas lista) ←←←
        # Por ahora usamos placeholder. Reemplaza cuando implementes odds_fetcher.py
        live_matches = []   # ← Reemplazar con: get_live_odds() o get_live_matches()

        if not live_matches:
            return ["✅ Bot profesional activo.\nNo hay partidos en vivo/próximos con odds disponibles en esta ejecución."]

        picks = []
        features_list = ["xg_diff", "factor_casa", "roi_home"]

        for match in live_matches[:10]:
            try:
                row = pd.DataFrame([{
                    'xg_diff': match.get('xg_home', 0) - match.get('xg_away', 0),
                    'factor_casa': 1.0,
                    'roi_home': 0.0
                }])
                
                row = calculate_features(row)
                X = row[features_list]
                
                prob_home = model.predict_proba(X)[0][1]
                odds_home = match.get('odds_home') or match.get('avg_odds_home') or match.get('odds_1', 2.0)
                
                implied_prob = 1 / odds_home
                value = prob_home - implied_prob
                
                if value > min_value and prob_home > min_prob:
                    stake = kelly_criterion(prob_home, odds_home, bankroll)
                    
                    if stake >= 5.0:   # Stake mínimo profesional
                        pick_text = (
                            f"🚨 **VALUE BET PROFESIONAL** 🚨\n"
                            f"**{match.get('home_team', 'Local')} vs {match.get('away_team', 'Visitante')}**\n"
                            f"Probabilidad modelo: **{prob_home:.1%}**\n"
                            f"Odds disponibles: **{odds_home:.2f}**\n"
                            f"Value detectado: **+{value:.1%}**\n"
                            f"Stake recomendado (Half-Kelly): **${stake}**\n"
                            f"Bankroll actual: ${bankroll}\n"
                            f"→ **Recomendación: Gana Local**"
                        )
                        picks.append(pick_text)
                        print(f"✅ Value fuerte encontrado | Stake ${stake}")

            except Exception as e:
                continue

        if not picks:
            return ["✅ Análisis profesional completado.\nNo se detectaron value bets con umbrales configurados en esta ejecución."]

        print(f"🎯 Generados {len(picks)} value picks de alto nivel")
        return picks

    except Exception as e:
        print(f"❌ Error en generate_picks: {e}")
        return [f"❌ Error técnico: {str(e)}"]

if __name__ == "__main__":
    picks = generate_picks(bankroll=1000)
    for p in picks:
        print("\n" + p)
