import os

# GitHub Secrets se cargan automáticamente en Actions
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SOFASCORE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Origin": "https://www.sofascore.com",
    "Referer": "https://www.sofascore.com/"
}

# Ligas populares (puedes agregar más)
LEAGUES = {
    "Premier League": {"tournament_id": 17, "odds_key": "soccer_epl"},
    "LaLiga": {"tournament_id": 8, "odds_key": "soccer_spain_la_liga"},
    "Bundesliga": {"tournament_id": 35, "odds_key": "soccer_germany_bundesliga"},
    "Serie A": {"tournament_id": 23, "odds_key": "soccer_italy_serie_a"},
    "Ligue 1": {"tournament_id": 34, "odds_key": "soccer_france_ligue_one"},
}
