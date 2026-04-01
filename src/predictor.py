import joblib
import pandas as pd
import os
from src.features import calculate_features

# Importa tus funciones existentes (ajusta los nombres si son diferentes)
try:
    from src.odds_fetcher import get_live_odds  # o get_upcoming_odds
except ImportError:
    def get_live_odds():
        print("⚠️ odds_fetcher no encontrado. Usando datos dummy.")
        return []

try:
    from src.sofascore_scraper import get_live_matches  # o similar
except ImportError:
    def get_live_matches():
        return []

def generate_picks(min_value=0.05, min_prob=0.52):
    model_path = "models/best_model.pkl"
    
    if not os.path.exists(model_path):
        print("⚠️ Modelo no encontrado.")
        return ["⚠️ Modelo no disponible. Ejecuta Retrain Model primero."]

    try:
        model = joblib.load(model_path)
        print(f"✅ Modelo cargado: {type(model).__name__}")

        # 1. Obtener partidos en vivo / próximos
        live_matches = get_live_odds() or get_live_matches()
        
        if not live_matches:
            print("ℹ️ No se encontraron partidos en vivo o próximos en esta ejecución.")
            return ["✅ Sistema listo. No hay partidos disponibles esta hora."]

        picks = []
        features_list = ["xg_diff", "factor_casa", "roi_home"]

        for match in live_matches[:10]:  # Limitamos para no saturar
            try:
                # Crear fila con datos del partido
                row = pd.DataFrame([{
                    'xg_diff': match.get('xg_home', 0) - match.get('xg_away', 0),
                    'factor_casa': 1.0,   # puedes mejorarlo con datos históricos
                    'roi_home': 0.0
                }])
                
                row = calculate_features(row)
                X = row[features_list]
                
                prob_home = model.predict_proba(X)[0][1]  # Probabilidad de que gane local
                
                # Odds (usa la mejor disponible)
                odds_home = match.get('odds_home') or match.get('avg_odds_home') or 2.0
                
                # Value bet simple: si la probabilidad del modelo > probabilidad implícita en las odds
                implied_prob = 1 / odds_home
                value = prob_home - implied_prob
                
                if value > min_value and prob_home > min_prob:
                    pick_text = (f"🚨 VALUE BET 🚨\n"
                                 f"{match.get('home_team', 'Local')} vs {match.get('away_team', 'Visitante')}\n"
                                 f"Prob modelo: {prob_home:.1%} | Odds: {odds_home:.2f}\n"
                                 f"Value: +{value:.1%} → Recomendado: Local gana")
                    picks.append(pick_text)
                    print(f"✅ Value encontrado: {match.get('home_team')} - prob {prob_home:.1%}")
            
            except Exception as e:
                print(f"Error procesando partido: {e}")
                continue

        if not picks:
            return ["✅ No se detectaron value bets con los umbrales actuales."]

        print(f"🎯 Generados {len(picks)} value picks")
        return picks

    except Exception as e:
        print(f"❌ Error general en generate_picks: {e}")
        return [f"❌ Error: {str(e)}"]

if __name__ == "__main__":
    picks = generate_picks()
    for p in picks:
        print(p)
