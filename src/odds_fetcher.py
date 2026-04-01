import requests
import pandas as pd
from src.config import ODDS_API_KEY

def get_odds(sport_key="soccer_epl", markets="h2h"):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu,us",
        "markets": markets,
        "oddsFormat": "decimal"
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print("Error Odds API:", resp.text)
        return pd.DataFrame()
    data = resp.json()
    rows = []
    for event in data:
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        rows.append({
                            "match_id": event["id"],
                            "home_team": event["home_team"],
                            "away_team": event["away_team"],
                            "commence_time": event["commence_time"],
                            "bookmaker": bookmaker["key"],
                            "market": outcome["name"],
                            "odd": outcome["price"]
                        })
    return pd.DataFrame(rows)
