from src.live_scanner import generate_picks  # o el que quieras
from src.notifier import send_telegram

picks = generate_picks()
print(picks)
if picks:
    send_telegram("\n".join(picks))
