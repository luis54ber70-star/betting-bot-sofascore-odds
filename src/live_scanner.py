import os
import pandas as pd
import joblib
import requests
from datetime import datetime, timedelta
import time

from src.features import calculate_features
from src.notifier import send_telegram   # asegúrate que este archivo exista

# ===================== CONFIG =====================
API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "soccer"                    # o "soccer_epl", "soccer_la_liga" para filtrar mejor
REGIONS = "eu"                      # "eu" suele tener mejores odds para fútbol europeo
MARKETS = "h2h"
ODDS_FORMAT = "decimal"             # decimal es más fácil para calcular edge

MIN_EDGE = 0.07                     # 7% edge mínimo (reduce mucha basura)
PROB_THRESHOLD = 0.54               # probabilidad mínima del modelo

MODEL_PATH = "models/best_model.pkl"

def load_model():
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Modelo no encontrado: {MODEL_PATH}")
        return None
    try:
        model = joblib.load(MODEL_PATH)
        print("✅ Modelo XGBoost cargado correctamente")
        return model
    except Exception as e:
        print(f"Error cargando modelo: {e}")
        return None


def get_odds():
    if not API_KEY:
        print("❌ ODDS_API_KEY no configurada")
        return None

    url = f"{BASE_URL}/sports/{SPORT}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": "iso"
    }

    try:
        resp = requests.get(url, params=params, timeout=20)
        print(f"Odds API: {resp.status_code} | Créditos restantes: {resp.headers.get('x-requests-remaining', 'N/A')}")

        if resp.status_code != 200:
            print(f"Error API: {resp.text[:500]}")
            return None

        return resp.json()
    except Exception as e:
        print(f"Error en petición Odds API: {e}")
        return None


def calculate_edge(prob_model: float, odds_decimal: float) -> float:
    if odds_decimal <= 1.01:
        return 0.0
    prob_implied = 1.0 / odds_decimal
    return prob_model - prob_implied


def process_and_scan():
    model = load_model()
    if model is None:
        send_telegram("⚠️ Error: No se pudo cargar el modelo")
        return

    odds_data = get_odds()
    if not odds_data:
        print("No se obtuvieron datos de odds esta hora.")
        return

    now = datetime.utcnow()
    alerts = []

    for event in odds_data:
        try:
            commence_time = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
            
            # Filtrar: solo próximos 3-24 horas (evita partidos ya jugados o muy lejanos)
            if commence_time < now or commence_time > now + timedelta(hours=24):
                continue

            home = event.get('home_team')
            away = event.get('away_team')
            if not home or not away:
                continue

            # Buscar mejor odd para victoria local (h2h)
            best_home_odds = None
            best_book = None

            for book in event.get('bookmakers', []):
                for market in book.get('markets', []):
                    if market.get('key') != 'h2h':
                        continue
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == home:
                            price = outcome.get('price')
                            if price and (best_home_odds is None or price > best_home_odds):
                                best_home_odds = price
                                best_book = book.get('title', 'Unknown')

            if not best_home_odds or best_home_odds < 1.3:  # evitar favoritos muy pesados (poca value)
                continue

            # Preparar datos para el modelo
            match_df = pd.DataFrame([{
                'home_team': home,
                'away_team': away,
                'home_team_goal_count': 0,
                'away_team_goal_count': 0,
                'xg_home': 1.2,      # valor promedio placeholder (puedes mejorarlo con scraper)
                'xg_away': 1.0,
            }])

            match_df = calculate_features(match_df)

            # Features que usa el modelo (ajusta si cambiaste en retrain_model)
            feature_cols = ["xg_diff", "factor_casa", "roi_home", "goal_diff", "xg_ratio"]
            available_features = [col for col in feature_cols if col in match_df.columns]
            X = match_df[available_features]

            prob_home_win = model.predict_proba(X)[0][1]

            if prob_home_win < PROB_THRESHOLD:
                continue

            edge = calculate_edge(prob_home_win, best_home_odds)

            if edge > MIN_EDGE:
                alert = (f"🔥 <b>VALUE PICK</b>\n\n"
                         f"<b>{home}</b> vs {away}\n"
                         f"Odds: <b>{best_home_odds:.2f}</b> @ {best_book}\n"
                         f"Prob Modelo: <b>{prob_home_win:.1%}</b>\n"
                         f"Edge: <b>+{edge:.1%}</b>\n"
                         f"Inicio: {commence_time.strftime('%H:%M UTC')}")
                alerts.append(alert)

        except Exception as e:
            # print(f"Error procesando evento: {e}")  # descomenta para debug
            continue

    # Enviar a Telegram
    if alerts:
        header = f"🏆 <b>BETTING BOT - {len(alerts)} VALUE PICKS</b> ({datetime.now().strftime('%d/%m %H:%M')})\n\n"
        full_message = header + "\n\n".join(alerts[:6])  # límite anti-spam
        send_telegram(full_message)
        print(f"✅ Enviados {len(alerts)} picks con edge a Telegram")
    else:
        print("ℹ️ No se encontraron picks con edge suficiente esta hora.")


if __name__ == "__main__":
    print(f"🚀 Live Scanner iniciado - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    process_and_scan()
