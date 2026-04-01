from src.predictor import generate_picks
from src.notifier import send_telegram

if __name__ == "__main__":
    print("🚀 Iniciando Live Scanner...")
    picks = generate_picks(bankroll=1000)
    
    if picks:
        msg = "🏆 **BETTING BOT - VALUE PICKS**\n\n" + "\n\n".join(picks)
        send_telegram(msg)
        print("✅ Picks enviados a Telegram")
    else:
        print("ℹ️ No hay picks esta hora")
