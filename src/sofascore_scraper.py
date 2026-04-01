import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_session_with_retries():
    """Crea sesión con reintentos automáticos para evitar bloqueos"""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[403, 429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

BASE_URL = "https://api.sofascore.com/api/v1"

def get_live_and_upcoming(limit_hours=24, leagues_focus=None):
    try:
        session = get_session_with_retries()
        url = f"{BASE_URL}/sport/football/scheduled-events"
        params = {"date": datetime.utcnow().strftime("%Y-%m-%d")}

        response = session.get(url, headers=HEADERS, params=params, timeout=20)
        
        if response.status_code != 200:
            print(f"Error SofaScore: {response.status_code}")
            if response.status_code == 403:
                print("⚠️ SofaScore bloqueó la solicitud (403). Intenta más tarde o verifica tu conexión.")
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

                if commence_time < now + timedelta(minutes=30) or commence_time > now + timedelta(hours=limit_hours):
                    continue

                home = event["homeTeam"]["name"]
                away = event["awayTeam"]["name"]
                league_id = event["tournament"]["id"]

                if leagues_focus and league_id not in leagues_focus:
                    continue

                match_id = event["id"]

                matches.append({
                    "match_id": match_id,
                    "home_team": home,
                    "away_team": away,
                    "commence_time": commence_time,
                    "home_team_goal_count": 0,
                    "away_team_goal_count": 0,
                    "xg_home": 0.0,
                    "xg_away": 0.0
                })
            except Exception:
                continue

        df = pd.DataFrame(matches)
        print(f"✅ SofaScore: {len(df)} partidos encontrados")
        return df

    except Exception as e:
        print(f"❌ Error en get_live_and_upcoming: {e}")
        return pd.DataFrame()


def get_match_statistics(match_id: int):
    try:
        session = get_session_with_retries()
        url = f"{BASE_URL}/event/{match_id}/statistics"
        response = session.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return None

        data = response.json()
        stats = {}

        for period in data.get("statistics", []):
            for group in period.get("groups", []):
                for item in group.get("items", []):
                    name = item.get("name", "").lower()
                    if ("expected" in name and "goal" in name) or "xg" in name:
                        if "home" in item and "away" in item:
                            stats["xg_home"] = float(item.get("home", 0))
                            stats["xg_away"] = float(item.get("away", 0))
                            return stats
        return stats if stats else None

    except Exception:
        return None


def enrich_with_xg(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    enriched = df.copy()
    for idx, row in enriched.iterrows():
        stats = get_match_statistics(row["match_id"])
        if stats:
            enriched.at[idx, "xg_home"] = stats.get("xg_home", 0.0)
            enriched.at[idx, "xg_away"] = stats.get("xg_away", 0.0)
        time.sleep(1.5)

    print(f"✅ Enriquecido con xG: {len(enriched)} partidos")
    return enriched