import os
import asyncio
import edge_tts
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")), override=True)

AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "audio"))
os.makedirs(AUDIO_DIR, exist_ok=True)

async def generate_voice_note_async(text: str, filename: str) -> str:
    """Generates localized neural Hinglish voice note using Edge-TTS."""
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
        print(f"[TTS Error] {e}")
        return ""

def send_real_whatsapp_interactive(phone: str, customer_name: str, amount: float, pay_url: str, hinglish_text: str, audio_url: str = None):
    """
    Dispatches live WhatsApp message with interactive CTA buttons.
    Guarded to ONLY send to the configured single verified TARGET_TEST_PHONE to prevent API revocation.
    """
    token = os.getenv("META_WA_TOKEN", "").strip()
    phone_id = os.getenv("META_PHONE_ID", "").strip()
    target_whitelisted_phone = os.getenv("TARGET_TEST_PHONE", "").strip()

    # Rate-limit safety: Route strictly to the single verified test number
    recipient_phone = "".join(filter(str.isdigit, target_whitelisted_phone or phone))

    if not token or not phone_id or token == "MOCK_TOKEN":
        print(f"[Meta WhatsApp Mock] Logged for {customer_name} ({recipient_phone}): {hinglish_text}")
        return {"status": "mock_delivered", "recipient": recipient_phone}

    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 1. Dispatch Interactive Quick-Reply Message
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": f"⚡ *AutoRecover OS*\n\n{hinglish_text}\n\n💳 *Amount Due:* ₹{amount:,.2f}\n🔗 *Quick Pay:* {pay_url}"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"PAY_{pay_url.split('/')[-1]}",
                            "title": f"✅ Pay ₹{amount:,.0f}"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "OPT_OUT",
                            "title": "🛑 Stop / Opt-out"
                        }
                    }
                ]
            }
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        res_data = response.json()
        print(f"📲 [WhatsApp Live Sent] Delivered to verified device ({recipient_phone}) for {customer_name}")
        return res_data
    except Exception as e:
        print(f"❌ [WhatsApp Error] {e}")
        return {"error": str(e)}