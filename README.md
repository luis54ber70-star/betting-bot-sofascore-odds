# Betting Bot Sofascore + The Odds API + ML

Sistema automático de picks y parlays en tiempo real.  
Analiza xG, factor casa, ROI histórico, forma, H2H y genera apuestas con edge > 10%.  
Se auto-entrena cada día con los resultados reales.

## Secrets necesarios en GitHub (Settings → Secrets and variables → Actions)
- `ODDS_API_KEY` → tu clave de The Odds API
- `TELEGRAM_BOT_TOKEN` → token de tu bot de Telegram
- `TELEGRAM_CHAT_ID` → tu chat ID personal

## Cómo ejecutarlo localmente
```bash
pip install -r requirements.txt
python run_local.py
