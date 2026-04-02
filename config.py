# =============================================================================
# CONFIGURACIÓN DEL BETTING BOT - 365Scores
# =============================================================================

# Configuración del scraper
SCRAPER_TYPE = "365scores"

# Configuración de 365Scores
365SCORES_API_KEY = ""
365SCORES_BASE_URL = "https://api.365scores.com"

# Configuración de Sofascore (backup)
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
BET_AMOUNT = 100

# Ligas a monitorear
TARGET_LEAGUES = [
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Champions League"
]

# Notificaciones
ENABLE_NOTIFICATIONS = True
NOTIFICATION_WEBHOOK = ""

# Logging
LOG_LEVEL = "INFO"
ENABLE_DEBUG = False
