from src.predictor import generate_picks
from src.notifier import send_telegram

if __name__ == "__main__":
    picks = generate_picks()
    if picks:
        msg = "🚨 NUEVOS PICKS EN VIVO 🚨\n\n" + "\n".join(picks)
        send_telegram(msg)
        print("Enviados a Telegram")
    else:
        print("No hay value bets esta hora")
