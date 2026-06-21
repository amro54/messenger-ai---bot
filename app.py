from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "mysecrettoken123"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge
    return "Invalid token", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event:
                    sender_id = event["sender"]["id"]
                    user_msg = event["message"].get("text", "")
                    if user_msg:
                        reply = ask_nvidia(user_msg)
                        send_message(sender_id, reply)
    return "OK", 200

def ask_nvidia(prompt):
    try:
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "moonshotai/kimi-k2.6",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
        r = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=body)
        return r.json()["choices"][0]["message"]["content"]
    except:
        return "عذراً، حدث خطأ"

def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    requests.post(url, json={"recipient": {"id": recipient_id}, "message": {"text": text}})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
