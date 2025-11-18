from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
from oaimain import ask_nutrition_agent

load_dotenv()

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_URL = "https://your-url.ngrok.io/webhook"  # We'll get this

@app.on_event("startup")
def set_webhook():
    """Set the webhook when FastAPI starts"""
    url = f"{BASE_URL}/setWebhook"
    resp = requests.post(url, json={"url": WEBHOOK_URL})
    print("Webhook set response:", resp.json())

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("Incoming:", data)

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_id = str(data["message"]["from"]["id"])
        text = data["message"].get("text", "").strip()

        if text.startswith('/start'):
            welcome = """🥗 *Nutrition Agent Started!*

Tell me what you ate and I'll analyze it!"""
            requests.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id, "text": welcome, "parse_mode": "Markdown"
            })
            return {"ok": True}

        # Use your nutrition agent
        try:
            reply = ask_nutrition_agent(text, user_id)
        except Exception as e:
            reply = "Sorry, I'm having trouble right now. Please try again!"

        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": chat_id, "text": reply, "parse_mode": "Markdown"
        })

    return {"ok": True}