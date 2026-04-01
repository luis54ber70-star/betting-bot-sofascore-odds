import requests
import pandas as pd
from datetime import datetime
from src.config import SOFASCORE_HEADERS, LEAGUES

def get_live_and_upcoming():
    url = "https://api.sofascore.com/api/v1/sport/football/live-events"
    resp = requests.get(url, headers=SOFASCORE_HEADERS)
    if resp.status_code != 200:
        return pd.DataFrame()
    data = resp.json()
    events = []
    for event in data.get("events", []):
        events.append({
            "match_id": event["id"],
            "tournament": event["tournament"]["name"],
            "home_team": event["homeTeam"]["name"],
            "away_team": event["awayTeam"]["name"],
            "start_time": datetime.fromtimestamp(event["startTimestamp"]),
            "status": event.get("status", {}).get("type", "notstarted")
        })
    return pd.DataFrame(events)

def get_match_statistics(match_id):
    url = f"https://api.sofascore.com/api/v1/event/{match_id}/statistics"
    resp = requests.get(url, headers=SOFASCORE_HEADERS)
    if resp.status_code != 200:
        return {}
    stats = resp.json()
    # Extrae xG si existe (Sofascore lo tiene en period 1 o 2)
    xg_home = xg_away = 0.0
    for period in stats.get("periods", []):
        for group in period.get("groups", []):
            if group["groupName"] == "Expected goals":
                for item in group["items"]:
                    if item["name"] == "Expected goals":
                        xg_home = item.get("home", 0.0)
                        xg_away = item.get("away", 0.0)
    return {"xg_home": xg_home, "xg_away": xg_away, "full_stats": stats}
