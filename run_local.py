# =============================================================================
# CONFIGURACIÓN DEL BETTING BOT - 365Scores
# =============================================================================

# Configuración del scraper
SCRAPER_TYPE = "365scores"  # Cambiado de "sofascore" a "365scores"

# Configuración de 365Scores
365SCORES_API_KEY = ""  # Tu API key de 365Scores (si requiere)
365SCORES_BASE_URL = "https://api.365scores.com"

# Configuración de Sofascore (mantener como backup)
SOFASCORE_BASE_URL = "https://api.sofascore.com"

# Configuración general
CHECK_INTERVAL_SECONDS = 60
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
LOG_FILE = "bot_log.txt"
DATA_FOLDER = "data"

# Configuración de apuestas
MIN_ODDS_THRESHOLD = 1.5
MAX_ODDS_THRESHOLD = 5.0
BET_AMOUNT = 100  # Unidades de apuesta

# Configuración de ligas a monitorear
TARGET_LEAGUES = [
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Champions League"
]

# Configuración de notificaciones
ENABLE_NOTIFICATIONS = True
NOTIFICATION_WEBHOOK = ""  # URL de webhook para notificaciones

# Logging
LOG_LEVEL = "INFO"
ENABLE_DEBUG = False
