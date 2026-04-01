import requests
import pandas as pd
import time
import json
from datetime import datetime, timedelta
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.sofascore.com/"
}

BASE_URL = "https://api.sofascore.com/api/v1"

def get_live_and_upcoming(limit_hours=24, leagues_focus=None):
    """
    Obtiene partidos en vivo y próximos (hasta limit_hours).
    leagues_focus: lista de IDs de ligas (opcional) para filtrar ruido.
    """
    try:
        # Endpoint para eventos de fútbol (soccer)
        url = f"{BASE_URL}/sport/football/scheduled-events"
        params = {
            "date": datetime.utcnow().strftime("%Y-%m-%d")  # hoy + próximos
        }

        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"Error SofaScore: {response.status_code} - {response.text[:300]}")
            return pd.DataFrame()

        data = response.json()
        events = data.get("events", [])

        matches = []
        now = datetime.utcnow()

        for event in events:
            try:
                start_ts = event.get("startTimestamp")
                if not start_ts:
                    continue
                commence_time = datetime.fromtimestamp(start_ts)

                # Filtrar: próximos 3 a 24 horas (evita ya jugados y muy lejanos)
                if commence_time < now + timedelta(minutes=30) or commence_time > now + timedelta(hours=limit_hours):
                    continue

                home = event["homeTeam"]["name"]
                away = event["awayTeam"]["name"]
                league = event["tournament"]["name"]
                league_id = event["tournament"]["id"]

                # Filtrar solo ligas top si se especifica
                if leagues_focus and league_id not in leagues_focus:
                    continue

                match_id = event["id"]
                status = event.get("status", {}).get("type", "upcoming")

                matches.append({
                    "match_id": match_id,
                    "home_team": home,
                    "away_team": away,
                    "league": league,
                    "commence_time": commence_time,
                    "status": status,
                    "home_team_goal_count": 0,   # placeholder (se actualiza si está live)
                    "away_team_goal_count": 0,
                    "xg_home": 0.0,
                    "xg_away": 0.0
                })
            except Exception:
                continue

        df = pd.DataFrame(matches)
        print(f"✅ SofaScore: {len(df)} partidos encontrados (live + próximos)")
        return df

    except Exception as e:
        print(f"❌ Error en get_live_and_upcoming: {e}")
        return pd.DataFrame()


def get_match_statistics(match_id: int):
    """
    Obtiene estadísticas detalladas de un partido (incluyendo xG cuando disponible).
    """
    try:
        url = f"{BASE_URL}/event/{match_id}/statistics"
        response = requests.get(url, headers=HEADERS, timeout=12)

        if response.status_code != 200:
            return None

        data = response.json()
        stats = {}

        # Buscar xG (expected goals) en las estadísticas
        for period in data.get("statistics", []):
            for group in period.get("groups", []):
                for item in group.get("items", []):
                    if "expectedGoals" in item.get("name", "").lower() or item.get("name") == "xG":
                        if "home" in item and "away" in item:
                            stats["xg_home"] = float(item.get("home", 0))
                            stats["xg_away"] = float(item.get("away", 0))
                            break

        # También podemos extraer posesión, tiros, etc. si quieres enriquecer más
        return stats if stats else None

    except Exception as e:
        print(f"Error obteniendo stats para match {match_id}: {e}")
        return None


# Función auxiliar para enriquecer DataFrame con xG
def enrich_with_xg(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    enriched = df.copy()
    for idx, row in enriched.iterrows():
        stats = get_match_statistics(row["match_id"])
        if stats:
            enriched.at[idx, "xg_home"] = stats.get("xg_home", 0.0)
            enriched.at[idx, "xg_away"] = stats.get("xg_away", 0.0)
        time.sleep(0.8)  # Delay para evitar bloqueo de SofaScore

    print(f"✅ Enriquecido con xG: {len(enriched)} partidos")
    return enriched
