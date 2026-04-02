# =============================================================================
# HISTORICAL DATA COLLECTOR - 365Scores
# =============================================================================

import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

# Import del nuevo scraper 365Scores
from 365scores_scraper import get_scraper
import config

class HistoricalCollector:
    """Colector de datos históricos usando 365Scores"""
    
    def __init__(self):
        self.scraper = get_scraper(api_key=config.365SCORES_API_KEY)
        self.data_folder = config.DATA_FOLDER
        self.log_file = config.LOG_FILE
        
        # Crear folder de datos si no existe
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
        self._log("HistoricalCollector initialized with 365Scores")
    
    def _log(self, message: str):
        """Guardar log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        if config.ENABLE_DEBUG:
            print(log_entry.strip())
    
    def collect_date(self, date_str: str) -> List[Dict]:
        """Colecionar datos de una fecha específica"""
        try:
            self._log(f"Collecting historical data for {date_str}")
            matches = self.scraper.get_historical_matches(date=date_str, sport="football")
            
            if matches:
                self._log(f"Found {len(matches)} matches for {date_str}")
                self._save_matches(matches, date_str)
            else:
                self._log(f"No matches found for {date_str}")
            
            return matches
        except Exception as e:
            self._log(f"Error collecting data for {date_str}: {str(e)}")
            return []
    
    def _save_matches(self, matches: List[Dict], date_str: str):
        """Guardar partidos en archivo JSON"""
        filename = f"{self.data_folder}/historical_{date_str}.json"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(matches, f, indent=2, ensure_ascii=False)
            self._log(f"Saved historical data to {filename}")
        except Exception as e:
            self._log(f"Error saving historical data: {str(e)}")
    
    def collect_range(self, start_date: str, end_date: str) -> int:
        """Colecionar datos para un rango de fechas"""
        total_matches = 0
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            matches = self.collect_date(date_str)
            total_matches += len(matches)
            
            current += timedelta(days=1)
            time.sleep(1)  # Evitar rate limiting
        
        self._log(f"Total matches collected: {total_matches}")
        return total_matches
    
    def collect_last_days(self, days: int = 7) -> int:
        """Colecionar datos de los últimos N días"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.collect_range(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )


def main():
    collector = HistoricalCollector()
    
    # Colecionar últimos 7 días por defecto
    total = collector.collect_last_days(days=7)
    print(f"Total matches collected: {total}")


if __name__ == "__main__":
    main()
