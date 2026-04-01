import os
import pandas as pd
import joblib
import requests
import time
from datetime import datetime, timedelta

# Importamos los módulos necesarios
from src.features import calculate_features
from src.sofascore_scraper import get_live_and_upcoming, enrich_with_xg
from src.notifier import send_telegram

# ===================== CONFIGURACIÓN =====================
API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "soccer"                    # Fútbol general
REGIONS = "eu"                      # Europa suele tener mejores odds para ligas top
MARKETS = "h2h"
ODDS_FORMAT = "decimal"

# Parámetros anti-basura (ajusta según veas resultados)
MIN_EDGE = 0.07                     # Edge mínimo del 7%
PROB_THRESHOLD = 0.54               # Probabilidad mínima del modelo

MODEL_PATH = "models/best_model.pkl"

# Opcional: Filtrar solo ligas importantes (IDs de SofaScore)
# Ejemplo: EPL=17, LaLiga=8, Bundesliga=35, Serie A=23, Ligue 1=34
LEAGUES_FOCUS = None  # Pon [17, 8, 35, 23, 34] si quieres solo las 5 grandes

# ========================================================

def load_model():
    """Carga el modelo XGBoost"""
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Modelo no encontrado en: {MODEL_PATH}")
        return None
    try:
        model = joblib.load(MODEL_PATH)
        print("✅ Modelo XGBoost cargado correctamente")
        return model
    except Exception as e:
        print(f"❌ Error al cargar modelo: {e}")
        return None


def get_odds():
    """Obtiene las odds desde The Odds API"""
    if not API_KEY:
        print("❌ ODDS_API_KEY no encontrada en variables de entorno")
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
        print(f"Odds API → Status: {resp.status_code} | Créditos restantes: {resp.headers.get('x-requests-remaining', 'N/A')}")

        if resp.status_code != 200:
            print(f"Error Odds API: {resp.text[:400]}")
            return None

        return resp.json()
    except Exception as e:
        print(f"❌ Error en petición a Odds API: {e}")
        return None


def calculate_edge(prob_model: float, odds_decimal: float) -> float:
    """Calcula el edge (value betting)"""
    if odds_decimal <= 1.01:
        return 0.0
    prob_implied = 1.0 / odds_decimal
    return prob_model - prob_implied


def process_and_scan():
    """Función principal: combina SofaScore + Odds API + Modelo"""
    model = load_model()
    if model is None:
        send_telegram("⚠️ Error crítico: No se pudo cargar el modelo")
        return

    print("📡 Obteniendo partidos desde SofaScore...")
    df_matches = get_live_and_upcoming(limit_hours=24, leagues_focus=LEAGUES_FOCUS)

    if df_matches.empty:
        print("⚠️ No se encontraron partidos relevantes en SofaScore.")
        return

    # Enriquecer con xG estimados de SofaScore
    print("🔬 Enriqueciendo con estadísticas y xG de SofaScore...")
    df_matches = enrich_with_xg(df_matches)

    # Obtener odds
    odds_data = get_odds()
    if not odds_data:
        print("⚠️ No se obtuvieron odds esta hora.")
        return

    now = datetime.utcnow()
    alerts = []

    print(f"Procesando {len(odds_data)} eventos de Odds API...")

    for event in odds_data:
        try:
            # Parsear hora de inicio
            commence_time = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))

            # Filtrar: solo partidos que empiezan entre 30 min y 24 horas
            if commence_time < now + timedelta(minutes=30) or commence_time > now + timedelta(hours=24):
                continue

            home = event.get('home_team')
            away = event.get('away_team')
            if not home or not away:
                continue

            # Buscar la mejor odd para victoria del local (h2h)
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

            if not best_home_odds or best_home_odds < 1.30:  # Evitar favoritos muy fuertes
                continue

            # Buscar datos de SofaScore para este partido
            match_row = df_matches[
                (df_matches['home_team'].str.contains(home, case=False, na=False)) &
                (df_matches['away_team'].str.contains(away, case=False, na=False))
            ]

            if match_row.empty:
                # Placeholder si no encontramos coincidencia exacta
                xg_home = 1.15
                xg_away = 1.05
            else:
                xg_home = match_row.iloc[0]['xg_home']
                xg_away = match_row.iloc[0]['xg_away']

            # Preparar datos para el modelo
            match_df = pd.DataFrame([{
                'home_team': home,
                'away_team': away,
                'home_team_goal_count': 0,
                'away_team_goal_count': 0,
                'xg_home': xg_home,
                'xg_away': xg_away,
            }])

            # Calcular features
            match_df = calculate_features(match_df)

            # Features que usa tu modelo (ajusta si cambiaste en retrain_model)
            feature_cols = ["xg_diff", "factor_casa", "roi_home", "goal_diff", "xg_ratio", "xg_total"]
            available_features = [col for col in feature_cols if col in match_df.columns]
            X = match_df[available_features]

            # Predicción
            prob_home_win = model.predict_proba(X)[0][1]

            if prob_home_win < PROB_THRESHOLD:
                continue

            edge = calculate_edge(prob_home_win, best_home_odds)

            if edge > MIN_EDGE:
                alert = (f"🔥 <b>VALUE PICK DETECTADO</b>\n\n"
                         f"<b>{home}</b> vs {away}\n"
                         f"Odds: <b>{best_home_odds:.2f}</b> @ {best_book}\n"
                         f"Prob Modelo: <b>{prob_home_win:.1%}</b>\n"
                         f"Edge: <b>+{edge:.1%}</b>\n"
                         f"Inicio: {commence_time.strftime('%H:%M UTC')}\n"
                         f"xG: {xg_home:.2f} - {xg_away:.2f}")
                alerts.append(alert)

        except Exception as e:
            continue  # Silencioso para no romper el loop

    # Enviar alertas por Telegram
    if alerts:
        header = f"🏆 <b>BETTING BOT — {len(alerts)} VALUE PICKS</b> ({datetime.now().strftime('%d/%m %H:%M')})\n\n"
        full_msg = header + "\n\n".join(alerts[:7])   # Límite para evitar spam
        send_telegram(full_msg)
        print(f"✅ {len(alerts)} picks con edge enviados a Telegram")
    else:
        print("ℹ️ No se encontraron picks con suficiente edge esta hora.")


if __name__ == "__main__":
    print(f"🚀 Live Scanner iniciado - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    process_and_scan()
