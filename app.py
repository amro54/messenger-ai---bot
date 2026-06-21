from flask import Flask, request
import requests
import os

app = Flask(__name__)

# تأكد من إضافة هذه المتغيرات في إعدادات Render (Environment)
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
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        payload = {
            "model": "moonshotai/kimi-k2.6",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 1.0
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ NVIDIA API Error: {e}")
        return "عذراً، حدث خطأ أثناء معالجة طلبك."

def send_message(recipient_id, text):
    try:
        url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
        headers = {"Content-Type": "application/json"}
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print(f"❌ Messenger Send Error: {e}")

if __name__ == "__main__":
    app.run()
