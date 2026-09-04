import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

token = os.getenv("META_WA_TOKEN", "").strip()
phone_id = os.getenv("META_PHONE_ID", "").strip()
phone = os.getenv("TARGET_TEST_PHONE", "").strip()

print(f"Using Phone ID: {phone_id}")
print(f"Target Recipient: {phone}")

if not token or not phone_id:
    print("❌ Token or Phone ID missing. Check your .env file.")
    exit()

url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Send Simple Text Message First to Verify Sandbox
payload = {
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": phone,
    "type": "text",
    "text": {
        "body": "⚡ AutoRecover OS: Test message from your local AI Engine."
    }
}

response = requests.post(url, json=payload, headers=headers, timeout=10)
print("Status Code:", response.status_code)
print("Response Body:", response.json())