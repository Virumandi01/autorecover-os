import os
import asyncio
import edge_tts
import requests

# Set your Meta WhatsApp Cloud API credentials in .env if available
META_WA_TOKEN = os.getenv("META_WA_TOKEN", "MOCK_TOKEN")
META_PHONE_ID = os.getenv("META_PHONE_ID", "10060934992384")
AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "audio"))
os.makedirs(AUDIO_DIR, exist_ok=True)

async def generate_voice_note_async(text: str, filename: str) -> str:
    """Uses Microsoft Neural Indian TTS (Hi-IN / En-IN) to generate voice notes."""
    output_path = os.path.join(AUDIO_DIR, f"{filename}.mp3")
    # Swara (Hindi Female) or Madhav (Hindi Male)
    communicate = edge_tts.Communicate(text, voice="hi-IN-SwaraNeural")
    await communicate.save(output_path)
    return output_path

def synthesize_hinglish_voice(text: str, txn_id: str) -> str:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(generate_voice_note_async(text, txn_id))
    except Exception as e:
        print(f"TTS synthesis error: {e}")
        return ""

def send_real_whatsapp_interactive(phone: str, customer_name: str, amount: float, pay_url: str, hinglish_text: str):
    """
    Dispatches WhatsApp Interactive message with 2 Quick-Reply CTA buttons:
    [ Proceed to Pay ₹X ] and [ Stop / Do Not Remind ]
    """
    if META_WA_TOKEN == "MOCK_TOKEN":
        print(f"[Meta WhatsApp Mock] Sent interactive nudge to {phone}: '{hinglish_text}' | Link: {pay_url}")
        return {"status": "dispatched_mock", "recipient": phone}

    url = f"https://graph.facebook.com/v19.0/{META_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": hinglish_text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": "ACT_PAY_NOW", "title": f"Pay ₹{amount:,.0f}"}
                    },
                    {
                        "type": "reply",
                        "reply": {"id": "ACT_OPT_OUT", "title": "Stop / Opt Out"}
                    }
                ]
            }
        }
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=5)
        return res.json()
    except Exception as e:
        print(f"WhatsApp Dispatch Error: {e}")
        return {"error": str(e)}

    