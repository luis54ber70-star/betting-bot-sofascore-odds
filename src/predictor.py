import joblib
import pandas as pd
import os
import requests
from src.features import calculate_features

def kelly_criterion(prob: float, odds: float, bankroll: float = 1000, fraction: float = 0.5) -> float:
    """Kelly Criterion Half-Kelly para mayor seguridad"""
    if odds <= 1.0 or prob <= 0 or prob >= 1:
        return 0.0
    b = odds - 1
    q = 1 - prob
    kelly = (prob * b - q) / b
    if kelly <= 0:
        return 0.0
    stake = kelly * fraction * bankroll
    return round(max(stake, 0), 2)

def get_live_and_upcoming_from_sofascore():
    """Obtiene partidos en vivo y próximos de SofaScore (Top 5 ligas)"""
    print("🔍 Buscando partidos en vivo y próximos en SofaScore...")
    try:
        # Endpoint público de SofaScore para eventos en vivo + próximos
        url = "https://api.sofascore.com/api/v1/sport/football/events/live"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()

        matches = []
        events = data.get("events", [])

        for event in events[:15]:  # Limitamos a 15 para no saturar
            try:
                status = event.get("status", {}).get("type", "")
                if status not in ["inprogress", "notstarted", "live"]:
                    continue  # Solo en vivo o por iniciar

                home_team = event["homeTeam"]["name"]
                away_team = event["awayTeam"]["name"]
                
                # Odds si SofaScore las muestra (a veces vienen en "odds")
                odds_home = 2.0
                if "odds" in event and event["odds"].get("1"):
                    odds_home = float(event["odds"]["1"])

                # xG aproximado si está disponible
                xg_home = event.get("homeTeam", {}).get("xG", 0) or 0.0
                xg_away = event.get("awayTeam", {}).get("xG", 0) or 0.0

                matches.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "xg_home": xg_home,
                    "xg_away": xg_away,
                    "odds_home": odds_home,
                    "status": status
                })
            except:
                continue

        print(f"✅ Encontrados {len(matches)} partidos en vivo/próximos")
        return matches

    except Exception as e:
        print(f"⚠️ Error al obtener datos de SofaScore: {e}")
        # Fallback: datos dummy para no romper el flujo
        return [
            {"home_team": "Equipo Local", "away_team": "Equipo Visitante", 
             "xg_home": 1.6, "xg_away": 1.1, "odds_home": 1.95, "status": "notstarted"}
        ]

def generate_picks(min_value: float = 0.04, min_prob: float = 0.53, bankroll: float = 1000):
    model_path = "models/best_model.pkl"
    
    if not os.path.exists(model_path):
        return ["⚠️ Modelo no encontrado."]

    try:
        model = joblib.load(model_path)
        print(f"✅ Modelo cargado: {type(model).__name__}")

        live_matches = get_live_and_upcoming_from_sofascore()

        if not live_matches:
            return ["✅ Bot activo (7AM-8PM).\nNo se encontraron partidos en vivo/próximos en esta ejecución."]

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
                            f"🚨 **VALUE BET** 🚨\n"
                            f"{status_emoji} {match['home_team']} vs {match['away_team']}\n"
                            f"Prob modelo: **{prob_home:.1%}**\n"
                            f"Odds: **{odds_home:.2f}**\n"
                            f"Value: **+{value:.1%}**\n"
                            f"Stake recomendado: **${stake}**"
                        )
                        picks.append(pick_text)
                        print(f"✅ Value encontrado: {match['home_team']} | Stake ${stake}")
            except Exception as e:
                continue

        return picks if picks else ["✅ Análisis completado.\nNo hay value bets con umbral actual esta hora."]

    except Exception as e:
        print(f"❌ Error en generate_picks: {e}")
        return ["❌ Error técnico al procesar picks."]

if __name__ == "__main__":
    picks = generate_picks(bankroll=1000)
    for p in picks:
        print("\n" + p)
