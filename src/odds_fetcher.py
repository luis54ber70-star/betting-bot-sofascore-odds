import requests
import pandas as pd
from src.config import ODDS_API_KEY

def get_live_odds(sport_key="soccer_epl", markets="h2h"):
    # Endpoint de odds
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu", # 'eu' suele tener mejores cuotas para ligas europeas y Liga MX
        "markets": markets,
        "oddsFormat": "decimal"
    }
    
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status() # Lanza error si el status no es 200
    except Exception as e:
        print(f"Error al conectar con Odds API: {e}")
        return pd.DataFrame()

    data = resp.json()
    rows = []
    
    for event in data:
        # Extraer info básica del evento
        event_id = event.get("id")
        home = event.get("home_team")
        away = event.get("away_team")
        start_time = event.get("commence_time")

        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                # Validamos el mercado solicitado
                if market["key"] == markets:
                    for outcome in market["outcomes"]:
                        rows.append({
                            "match_id": event_id,
                            "home_team": home,
                            "away_team": away,
                            "commence_time": start_time,
                            "bookmaker": bookmaker["key"],
                            "market_type": markets,
                            "selection": outcome["name"],
                            "odd": outcome["price"]
                        })
                        
    return pd.DataFrame(rows)
