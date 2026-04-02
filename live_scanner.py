# =============================================================================
# LIVE SCANNER - 365Scores
# =============================================================================

import time
import json
import os
from datetime import datetime
from typing import List, Dict

from 365scores_scraper import get_scraper
import config

class LiveScanner:
    """Escáner de partidos en vivo usando 365Scores"""
    
    def __init__(self):
        self.scraper = get_scraper(api_key=config.365SCORES_API_KEY)
        self.data_folder = config.DATA_FOLDER
        self.log_file = config.LOG_FILE
        
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
        self._log("LiveScanner initialized with 365Scores")
    
    def _log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        if config.ENABLE_DEBUG:
            print(log_entry.strip())
    
    def scan_live_matches(self) -> List[Dict]:
        try:
            self._log("Starting live match scan...")
            matches = self.scraper.get_live_matches(sport="football")
            
            if matches:
                self._log(f"Found {len(matches)} live matches")
                self._save_matches(matches)
            else:
                self._log("No live matches found")
            
            return matches
        except Exception as e:
            self._log(f"Error scanning live matches: {str(e)}")
            return []
    
    def _save_matches(self, matches: List[Dict]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.data_folder}/live_matches_{timestamp}.json"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(matches, f, indent=2, ensure_ascii=False)
            self._log(f"Saved matches to {filename}")
        except Exception as e:
            self._log(f"Error saving matches: {str(e)}")
    
    def analyze_odds(self, matches: List[Dict]) -> List[Dict]:
        opportunities = []
        
        for match in matches:
            odds = match.get('odds', {})
            
            if odds.get('home_win') and odds.get('away_win'):
                if config.MIN_ODDS_THRESHOLD <= odds['home_win'] <= config.MAX_ODDS_THRESHOLD:
                    opportunities.append({
                        'match_id': match.get('match_id'),
                        'home_team': match.get('home_team'),
                        'away_team': match.get('away_team'),
                        'league': match.get('league'),
                        'bet_type': 'home_win',
                        'odds': odds['home_win'],
                        'timestamp': datetime.now().isoformat()
                    })
                
                if config.MIN_ODDS_THRESHOLD <= odds['away_win'] <= config.MAX_ODDS_THRESHOLD:
                    opportunities.append({
                        'match_id': match.get('match_id'),
                        'home_team': match.get('home_team'),
                        'away_team': match.get('away_team'),
                        'league': match.get('league'),
                        'bet_type': 'away_win',
                        'odds': odds['away_win'],
                        'timestamp': datetime.now().isoformat()
                    })
        
        self._log(f"Found {len(opportunities)} betting opportunities")
        return opportunities
    
    def run(self):
        self._log("LiveScanner started")
        
        try:
            while True:
                matches = self.scan_live_matches()
                if matches:
                    opportunities = self.analyze_odds(matches)
                    if opportunities:
                        self._log(f"Opportunities found: {len(opportunities)}")
                
                time.sleep(config.CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            self._log("LiveScanner stopped by user")
        except Exception as e:
            self._log(f"LiveScanner error: {str(e)}")


def main():
    scanner = LiveScanner()
    scanner.run()


if __name__ == "__main__":
    main()
