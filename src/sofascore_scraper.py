import requests
import pandas as pd
import time
import logging
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================
RESPONSE_TIMEOUT = 20
STATS_TIMEOUT = 15
API_CALL_DELAY = 1.5
MIN_MATCH_OFFSET_MINUTES = 30
RETRY_BACKOFF_FACTOR = 2
RETRY_STATUS_CODES = [403, 429, 500, 502, 503, 504]
RETRY_TOTAL_ATTEMPTS = 5

BASE_URL = "https://api.sofascore.com/api/v1"

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

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# SESSION MANAGEMENT (Thread-Safe Global Session)
# ============================================================================
_session: Optional[requests.Session] = None
_session_lock = threading.Lock()

def get_session_with_retries() -> requests.Session:
    """
    Retorna una sesión reutilizable con reintentos automáticos.
    Thread-safe para uso concurrente. Evita crear múltiples sesiones innecesarias.
    
    Returns:
        requests.Session: Sesión configurada con reintentos automáticos
    """
    global _session
    
    if _session is None:
        with _session_lock:
            if _session is None:  # Double-check pattern
                _session = requests.Session()
                retry = Retry(
                    total=RETRY_TOTAL_ATTEMPTS,
                    backoff_factor=RETRY_BACKOFF_FACTOR,
                    status_forcelist=RETRY_STATUS_CODES
                )
                adapter = HTTPAdapter(max_retries=retry)
                _session.mount('http://', adapter)
                _session.mount('https://', adapter)
                logger.debug("Nueva sesión con reintentos creada")
    
    return _session

def close_session() -> None:
    """Cierra la sesión global reutilizable de forma segura"""
    global _session
    with _session_lock:
        if _session is not None:
            _session.close()
            _session = None
            logger.debug("Sesión cerrada")

# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def get_live_and_upcoming(
    limit_hours: int = 24,
    leagues_focus: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Obtiene partidos próximos y en vivo desde SofaScore API.
    
    Args:
        limit_hours (int): Horas máximas hacia adelante para buscar partidos.
                          Debe ser positivo. Default: 24
        leagues_focus (Optional[List[int]]): IDs de ligas a filtrar (opcional).
                                             Default: None (sin filtro)
    
    Returns:
        pd.DataFrame: DataFrame con partidos encontrados o vacío en caso de error.
                     Columnas: match_id, home_team, away_team, commence_time,
                               home_team_goal_count, away_team_goal_count, xg_home, xg_away
    
    Raises:
        ValueError: Si limit_hours no es positivo
        TypeError: Si leagues_focus no es una lista
    
    Examples:
        >>> df = get_live_and_upcoming(limit_hours=24)
        >>> df = get_live_and_upcoming(limit_hours=48, leagues_focus=[1234, 5678])
    """
    # Input validation
    if not isinstance(limit_hours, int) or limit_hours <= 0:
        raise ValueError(f"limit_hours debe ser un entero positivo, recibido: {limit_hours}")
    
    if leagues_focus is not None and not isinstance(leagues_focus, list):
        raise TypeError(f"leagues_focus debe ser una lista, recibido: {type(leagues_focus)}")
    
    try:
        session = get_session_with_retries()
        url = f"{BASE_URL}/sport/football/scheduled-events"
        params = {"date": datetime.utcnow().strftime("%Y-%m-%d")}
        
        logger.info(f"Obteniendo partidos de SofaScore (próximas {limit_hours} horas)...")
        response = session.get(url, headers=HEADERS, params=params, timeout=RESPONSE_TIMEOUT)
        
        # Usar raise_for_status() en lugar de chequeos manuales
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP en SofaScore API: {response.status_code}")
            if response.status_code == 403:
                logger.warning("⚠️ SofaScore bloqueó la solicitud (403). Intenta más tarde o verifica tu conexión.")
            elif response.status_code == 429:
                logger.warning("⚠️ Límite de solicitudes alcanzado. Espera antes de reintentar.")
            return pd.DataFrame()
        
        data = response.json()
        events = data.get("events", [])
        logger.debug(f"API retornó {len(events)} eventos")
        
        matches: List[Dict[str, Any]] = []
        now = datetime.utcnow()
        min_time = now + timedelta(minutes=MIN_MATCH_OFFSET_MINUTES)
        max_time = now + timedelta(hours=limit_hours)
        
        # Procesar cada evento con manejo específico de excepciones
        for event in events:
            try:
                # Validar timestamp
                start_ts = event.get("startTimestamp")
                if not start_ts:
                    logger.debug("Evento sin timestamp, ignorado")
                    continue
                
                commence_time = datetime.fromtimestamp(start_ts)
                
                # Filtrar por ventana de tiempo
                if not (min_time <= commence_time <= max_time):
                    continue
                
                # Extraer datos con manejo de KeyError específico
                try:
                    home = event["homeTeam"]["name"]
                    away = event["awayTeam"]["name"]
                    league_id = event["tournament"]["id"]
                except KeyError as e:
                    logger.debug(f"Datos faltantes en evento: {e}")
                    continue
                
                # Filtrar por liga si es necesario
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
                
            except (TypeError, ValueError) as e:
                logger.debug(f"Error procesando evento: {e}")
                continue
        
        df = pd.DataFrame(matches)
        logger.info(f"✅ SofaScore: {len(df)} partidos encontrados")
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error de conexión en get_live_and_upcoming: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Error inesperado en get_live_and_upcoming: {e}", exc_info=True)
        return pd.DataFrame()


def get_match_statistics(match_id: int) -> Optional[Dict[str, float]]:
    """
    Obtiene estadísticas de un partido específico (xG, etc).
    
    Args:
        match_id (int): ID del partido en SofaScore. Debe ser positivo.
    
    Returns:
        Optional[Dict[str, float]]: Diccionario con claves 'xg_home' y 'xg_away',
                                   o None si no hay datos disponibles
    
    Raises:
        ValueError: Si match_id no es válido (no es positivo)
        TypeError: Si match_id no es un entero
    
    Examples:
        >>> stats = get_match_statistics(12345678)
        >>> print(stats)
        {'xg_home': 1.5, 'xg_away': 0.8}
    """
    # Input validation
    if not isinstance(match_id, int):
        raise TypeError(f"match_id debe ser un entero, recibido: {type(match_id)}")
    if match_id <= 0:
        raise ValueError(f"match_id debe ser positivo, recibido: {match_id}")
    
    try:
        session = get_session_with_retries()
        url = f"{BASE_URL}/event/{match_id}/statistics"
        
        response = session.get(url, headers=HEADERS, timeout=STATS_TIMEOUT)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.debug(f"No se obtuvieron estadísticas para match_id {match_id}: {response.status_code}")
            return None
        
        data = response.json()
        stats: Dict[str, float] = {}
        
        # Buscar xG en las estadísticas con mejor estructura
        statistics = data.get("statistics", [])
        for period in statistics:
            groups = period.get("groups", [])
            for group in groups:
                items = group.get("items", [])
                for item in items:
                    name = item.get("name", "").lower()
                    
                    # Detectar campos de xG
                    if ("expected" in name and "goal" in name) or "xg" in name:
                        try:
                            home_val = item.get("home")
                            away_val = item.get("away")
                            
                            if home_val is not None and away_val is not None:
                                stats["xg_home"] = float(home_val)
                                stats["xg_away"] = float(away_val)
                                logger.debug(f"xG encontrado para match_id {match_id}: {stats}")
                                return stats
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error convirtiendo xG a float para match_id {match_id}: {e}")
                            continue
        
        return stats if stats else None
        
    except requests.exceptions.RequestException as e:
        logger.debug(f"Error de conexión obteniendo estadísticas para match_id {match_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado en get_match_statistics({match_id}): {e}", exc_info=True)
        return None


def enrich_with_xg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriquece DataFrame con datos de xG (Expected Goals).
    Usa operaciones vectorizadas para optimizar rendimiento.
    
    Args:
        df (pd.DataFrame): DataFrame con columna 'match_id'.
                          Debe contener columnas: match_id, xg_home, xg_away
    
    Returns:
        pd.DataFrame: DataFrame enriquecido con xG actualizado.
                     Retorna el mismo DataFrame si está vacío.
    
    Raises:
        ValueError: Si el DataFrame no contiene la columna 'match_id'
    
    Examples:
        >>> df = get_live_and_upcoming()
        >>> df_enriched = enrich_with_xg(df)
    """
    if df.empty:
        logger.warning("DataFrame vacío, no hay nada que enriquecer")
        return df
    
    # Validar que exista la columna match_id
    if "match_id" not in df.columns:
        raise ValueError("DataFrame debe contener columna 'match_id'")
    
    logger.info(f"Enriqueciendo {len(df)} partidos con xG...")
    
    enriched = df.copy()
    xg_results: List[Dict[str, float]] = []
    
    try:
        match_ids = enriched["match_id"].tolist()
        
        for idx, match_id in enumerate(match_ids, 1):
            try:
                stats = get_match_statistics(match_id)
                
                if stats:
                    xg_results.append({
                        "xg_home": stats.get("xg_home", 0.0),
                        "xg_away": stats.get("xg_away", 0.0)
                    })
                else:
                    xg_results.append({"xg_home": 0.0, "xg_away": 0.0})
                
                logger.debug(f"[{idx}/{len(match_ids)}] Procesado match_id {match_id}")
                
            except Exception as e:
                logger.warning(f"Error obteniendo xG para match_id {match_id}: {e}")
                xg_results.append({"xg_home": 0.0, "xg_away": 0.0})
            
            # Rate limiting
            time.sleep(API_CALL_DELAY)
        
        # Operación vectorizada (mucho más rápida que iterrows + at[])
        if xg_results:
            xg_df = pd.DataFrame(xg_results, index=enriched.index)
            enriched[["xg_home", "xg_away"]] = xg_df[["xg_home", "xg_away"]]
        
        logger.info(f"✅ Enriquecido con xG: {len(enriched)} partidos")
        return enriched
        
    except Exception as e:
        logger.error(f"❌ Error en enrich_with_xg: {e}", exc_info=True)
        return enriched
