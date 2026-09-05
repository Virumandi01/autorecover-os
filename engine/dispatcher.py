import os
import asyncio
import edge_tts
import requests
from dotenv import load_dotenv

# Ensure fresh environment load
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")), override=True)

AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "audio"))
os.makedirs(AUDIO_DIR, exist_ok=True)

async def generate_voice_note_async(text: str, filename: str) -> str:
    output_path = os.path.join(AUDIO_DIR, f"{filename}.mp3")
    communicate = edge_tts.Communicate(text, voice="hi-IN-SwaraNeural")
    await communicate.save(output_path)
    return output_path

def synthesize_hinglish_voice(text: str, txn_id: str) -> str:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(generate_voice_note_async(text, txn_id))
    except Exception as e:
        print(f"⚠️ [TTS Error] {e}")
        return ""

def send_real_whatsapp_interactive(phone: str, customer_name: str, amount: float, pay_url: str, hinglish_text: str, txn_id: str = "TXN_LIVE", send_voice: bool = True):
    token = os.getenv("META_WA_TOKEN", "").strip()
    phone_id = os.getenv("META_PHONE_ID", "").strip()
    target_whitelisted_phone = os.getenv("TARGET_TEST_PHONE", "").strip()
    public_base_url = os.getenv("PUBLIC_SERVER_URL", "").strip().rstrip("/")

    # Sanitize recipient number
    raw_num = target_whitelisted_phone if target_whitelisted_phone else phone
    recipient_phone = "".join(filter(str.isdigit, raw_num))

    if not token or not phone_id:
        print("⚠️ [Meta API] Missing META_WA_TOKEN or META_PHONE_ID in .env")
        return {"error": "missing_credentials"}

    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 1. Attempt Audio Voice Note Dispatch if Public URL is valid
    if send_voice and public_base_url and txn_id and not public_base_url.startswith("http://localhost"):
        audio_link = f"{public_base_url}/static/audio/{txn_id}.mp3"
        audio_payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "audio",
            "audio": {"link": audio_link}
        }
        try:
            res_audio = requests.post(url, json=audio_payload, headers=headers, timeout=8)
            print(f"🔊 [WhatsApp Audio] Status: {res_audio.status_code}")
        except Exception as e:
            print(f"⚠️ [WhatsApp Audio Dispatch Failed] {e}")

    # 2. Interactive CTA Button Dispatch
    # WhatsApp button title constraint: Max 20 characters
    pay_btn_title = f"Pay ₹{amount:,.0f}"[:20]
    stop_btn_title = "Stop / Cancel"[:20]

    clean_text = (
        f"⚡ *AutoRecover OS Alert*\n\n"
        f"Customer: {customer_name}\n"
        f"Amount Due: ₹{amount:,.2f}\n"
        f"Txn ID: {txn_id}\n\n"
        f"_{hinglish_text}_"
    )

    interactive_payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": clean_text
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"PAY_{txn_id}",
                            "title": pay_btn_title
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"OPT_OUT_{txn_id}",
                            "title": stop_btn_title
                        }
                    }
                ]
            }
        }
    }

    try:
        res = requests.post(url, json=interactive_payload, headers=headers, timeout=10)
        print(f"💬 [WhatsApp Interactive] Status: {res.status_code}")
        
        # If interactive payload fails, fallback immediately to clean text
        if res.status_code != 200:
            print(f"⚠️ [Meta Interactive Rejected: {res.text}]. Falling back to standard text...")
            fallback_payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient_phone,
                "type": "text",
                "text": {"body": f"{clean_text}\n\n👉 Pay Now: {pay_url}"}
            }
            res_fb = requests.post(url, json=fallback_payload, headers=headers, timeout=10)
            return res_fb.json()
            
        return res.json()
    except Exception as e:
        print(f"❌ [Dispatch Error] {e}")
        return {"error": str(e)}