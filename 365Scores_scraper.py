import requests
import time
from datetime import datetime
from typing import List, Dict, Optional

class ThreeSixFiveScoresScraper:
    """Scraper para obtener datos de 365Scores"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.365scores.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    def get_live_matches(self, sport: str = "football") -> List[Dict]:
        """Obtener partidos en vivo"""
        try:
            url = f"{self.base_url}/v1/matches/live"
            params = {'sport': sport}
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            matches = []
            for match in data.get('matches', []):
                matches.append({
                    'match_id': match.get('id'),
                    'home_team': match.get('homeTeam', {}).get('name'),
                    'away_team': match.get('awayTeam', {}).get('name'),
                    'home_score': match.get('homeScore'),
                    'away_score': match.get('awayScore'),
                    'status': match.get('status'),
                    'minute': match.get('minute'),
                    'league': match.get('competition', {}).get('name'),
                    'country': match.get('competition', {}).get('country'),
                    'start_time': match.get('startTime'),
                    'odds': self._extract_odds(match.get('odds', {}))
                })
            return matches
        except Exception as e:
            print(f"Error obteniendo partidos en vivo: {str(e)}")
            return []
    
    def get_match_odds(self, match_id: str) -> Dict:
        """Obtener cuotas específicas de un partido"""
        try:
            url = f"{self.base_url}/v1/matches/{match_id}/odds"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return self._extract_odds(data.get('odds', {}))
        except Exception as e:
            print(f"Error obteniendo cuotas: {str(e)}")
            return {}
    
    def _extract_odds(self, odds_data: Dict) -> Dict:
        """Extraer y normalizar las cuotas"""
        normalized_odds = {
            'home_win': None,
            'draw': None,
            'away_win': None,
            'over_2_5': None,
            'under_2_5': None,
            'both_teams_score': None,
            'timestamp': datetime.now().isoformat()
        }
        
        if isinstance(odds_data, dict):
            for bookmaker, markets in odds_data.items():
                if isinstance(markets, dict):
                    if '1X2' in markets or 'match_winner' in markets:
                        market = markets.get('1X2') or markets.get('match_winner')
                        if isinstance(market, dict):
                            normalized_odds['home_win'] = market.get('1') or market.get('home')
                            normalized_odds['draw'] = market.get('X') or market.get('draw')
                            normalized_odds['away_win'] = market.get('2') or market.get('away')
                    
                    if 'over_under' in markets or 'totals' in markets:
                        market = markets.get('over_under') or markets.get('totals')
                        if isinstance(market, dict):
                            normalized_odds['over_2_5'] = market.get('over_2.5') or market.get('over')
                            normalized_odds['under_2_5'] = market.get('under_2.5') or market.get('under')
                    
                    if 'both_teams_score' in markets or 'btts' in markets:
                        market = markets.get('both_teams_score') or markets.get('btts')
                        if isinstance(market, dict):
                            normalized_odds['both_teams_score'] = market.get('yes')
        
        return normalized_odds
    
    def get_historical_matches(self, date: str, sport: str = "football") -> List[Dict]:
        """Obtener partidos históricos por fecha"""
        try:
            url = f"{self.base_url}/v1/matches/historical"
            params = {'date': date, 'sport': sport}
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            matches = []
            for match in data.get('matches', []):
                matches.append({
                    'match_id': match.get('id'),
                    'home_team': match.get('homeTeam', {}).get('name'),
                    'away_team': match.get('awayTeam', {}).get('name'),
                    'home_score': match.get('homeScore'),
                    'away_score': match.get('awayScore'),
                    'status': 'finished',
                    'league': match.get('competition', {}).get('name'),
                    'start_time': match.get('startTime'),
                    'odds': self._extract_odds(match.get('odds', {}))
                })
            return matches
        except Exception as e:
            print(f"Error obteniendo históricos: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """Probar conexión con la API"""
        try:
            response = self.session.get(f"{self.base_url}/v1/health", timeout=10)
            return response.status_code == 200
        except:
            return False


# Función de conveniencia para obtener instancia
def get_scraper(api_key: str = None) -> ThreeSixFiveScoresScraper:
    return ThreeSixFiveScoresScraper(api_key=api_key)
