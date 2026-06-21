from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "mysecrettoken123"
# تأكد من إضافة هذه المتغيرات في إعدادات الاستضافة
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
                        # 1. إرسال النص إلى NVIDIA
                        reply = ask_nvidia(user_msg)
                        # 2. إرسال الرد إلى المستخدم في ماسنجر
                        send_message(sender_id, reply)
    return "OK", 200

def ask_nvidia(prompt):
    try:
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # رابط API الخاص بـ NVIDIA (تأكد من استخدام الرابط الصحيح للنموذج الذي تريده)
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        payload = {
            "model": "meta/llama3-8b-instruct", # ضع اسم النموذج الصحيح الذي تستخدمه هنا
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # هذه الدالة ستلتقط أي خطأ في الاتصال (مثل 401 أو 500)
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
        
    except Exception as e:
        # طباعة الخطأ الفعلي في سجلات الخادم لتعرف السبب المباشر
        print(f"❌ NVIDIA API Error: {e}")
        return "عذراً، حدث خطأ أثناء معالجة طلبك."

def send_message(recipient_id, text):
    try:
        # تأكد من استخدام إصدار Graph API المناسب (هنا v19.0 كمثال)
        url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
    except Exception as e:
        print(f"❌ Messenger Send Error: {e}")
