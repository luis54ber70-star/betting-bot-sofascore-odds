import os
import pandas as pd
import joblib
import requests
from datetime import datetime, timedelta
import time
from src.features import calculate_features  # Asumimos que existe
from src.notifier import send_telegram

# ===================== CONFIG =====================
API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "soccer"                    # Para fútbol general (o "soccer_epl", "soccer_la_liga", etc. si quieres específico)
REGIONS = "eu,us"                   # Ajusta según tus bookies preferidos (eu suele tener mejores odds para Europa)
MARKETS = "h2h"                     # Solo moneyline por ahora (puedes añadir spreads,totals después)
ODDS_FORMAT = "decimal"             # Más fácil de trabajar con decimal

MIN_EDGE = 0.07                     # 7% de edge mínimo → reduce mucha basura
PROB_THRESHOLD = 0.55               # Probabilidad mínima del modelo

MODEL_PATH = "models/best_model.pkl"

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram no configurado")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error Telegram: {e}")


def load_model():
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Modelo no encontrado en {MODEL_PATH}")
        return None
    model = joblib.load(MODEL_PATH)
    print("✅ Modelo XGBoost cargado correctamente")
    return model


def get_odds():
    if not API_KEY:
        print("❌ ODDS_API_KEY no encontrada")
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
        resp = requests.get(url, params=params, timeout=15)
        print(f"API Status: {resp.status_code} | Créditos restantes: {resp.headers.get('x-requests-remaining', 'N/A')}")

        if resp.status_code != 200:
            print(f"Error API: {resp.text}")
            return None

        return resp.json()
    except Exception as e:
        print(f"Error en petición Odds API: {e}")
        return None


def calculate_edge(prob_model: float, odds_decimal: float) -> float:
    """Calcula el edge (value)"""
    if odds_decimal <= 1.0:
        return 0.0
    prob_implied = 1.0 / odds_decimal
    return prob_model - prob_implied


def process_and_scan():
    model = load_model()
    if model is None:
        send_telegram("⚠️ Error crítico: Modelo no encontrado")
        return

    odds_data = get_odds()
    if not odds_data:
        print("No se obtuvieron odds esta hora")
        return

    now = datetime.utcnow()
    alerts = []

    for event in odds_data:
        commence_str = event.get('commence_time')
        if not commence_str:
            continue
        try:
            commence_time = datetime.fromisoformat(commence_str.replace('Z', '+00:00'))
        except:
            continue

        # Solo partidos que empiezan en las próximas 2-24 horas (evita live y muy lejanos)
        if commence_time < now or commence_time > now + timedelta(hours=24):
            continue

        home = event.get('home_team')
        away = event.get('away_team')
        if not home or not away:
            continue

        # Buscar la mejor odd para home win (h2h)
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
                            best_book = book.get('title')

        if not best_home_odds:
            continue

        # Crear fila para predecir (debes adaptar calculate_features)
        match_df = pd.DataFrame([{
            'home_team': home,
            'away_team': away,
            'home_team_goal_count': 0,   # Placeholder (no tenemos resultado aún)
            'away_team_goal_count': 0,
            'xg_home': 0.0,              # Idealmente obtendrías de SofaScore o otro source
            'xg_away': 0.0,
        }])

        try:
            match_df = calculate_features(match_df)
            features = ["xg_diff", "factor_casa", "roi_home"]
            X = match_df[features]

            prob_home_win = model.predict_proba(X)[0][1]   # Probabilidad de que gane local

            if prob_home_win < PROB_THRESHOLD:
                continue

            edge = calculate_edge(prob_home_win, best_home_odds)

            if edge > MIN_EDGE:
                alert = (f"🔥 <b>VALUE PICK DETECTADO</b>\n\n"
                         f"<b>{home}</b> vs {away}\n"
                         f"Odds: <b>{best_home_odds:.2f}</b> ({best_book})\n"
                         f"Prob Modelo: <b>{prob_home_win:.1%}</b>\n"
                         f"Edge: <b>+{edge:.1%}</b>\n"
                         f"Hora: {commence_time.strftime('%Y-%m-%d %H:%M UTC')}")
                alerts.append(alert)

        except Exception as e:
            print(f"Error procesando partido {home} vs {away}: {e}")
            continue

    # Enviar alertas
    if alerts:
        header = f"🏆 <b>BETTING BOT - {len(alerts)} VALUE PICKS</b> ({datetime.now().strftime('%H:%M')})\n\n"
        full_msg = header + "\n\n".join(alerts[:8])  # límite para no spamear
        send_telegram(full_msg)
        print(f"✅ {len(alerts)} picks con edge enviados a Telegram")
    else:
        print("ℹ️ No se encontraron picks con suficiente edge esta hora.")


if __name__ == "__main__":
    print(f"🚀 Live Scanner iniciado - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    process_and_scan()
