from src.predictor import generate_picks
from src.notifier import send_telegram

if __name__ == "__main__":
    print("🚀 Iniciando Live Scanner...")
    picks = generate_picks()
    
    if picks:
        msg = "🚨 NUEVOS PICKS EN VIVO 🚨\n\n" + "\n".join(picks)
        send_telegram(msg)
        print("✅ Picks enviados a Telegram")
    else:
        print("ℹ️ No hay value bets en esta ejecución")
