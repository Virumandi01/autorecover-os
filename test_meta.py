import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

token = os.getenv("META_WA_TOKEN", "").strip()
phone_id = os.getenv("META_PHONE_ID", "").strip()
to_phone = os.getenv("TARGET_TEST_PHONE", "").strip()

print(f"🔍 Testing Meta Dispatch...")
print(f"Phone ID: {phone_id}")
print(f"Target Phone: {to_phone}")
print(f"Token (First 15 chars): {token[:15]}...")

url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": to_phone,
    "type": "text",
    "text": {"body": "⚡ AutoRecover OS: Diagnostic Ping"}
}

res = requests.post(url, json=payload, headers=headers)
print(f"\nStatus Code: {res.status_code}")
print(f"Response: {res.text}")