import os
import json
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from db import finalize_transaction, get_db

app = FastAPI()

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
os.makedirs(os.path.join(STATIC_DIR, "audio"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

WEBHOOK_VERIFY_TOKEN = "AUTORECOVER_SECRET_123"

@app.get("/")
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode") or params.get("hub_mode")
    token = params.get("hub.verify_token") or params.get("hub_verify_token")
    challenge = params.get("hub.challenge") or params.get("hub_challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print(f"✅ [Meta Handshake OK] Validated challenge: {challenge}")
        return Response(content=str(challenge), media_type="text/plain")
    return Response(content="Forbidden", status_code=403)

@app.post("/")
@app.post("/webhook")
async def handle_whatsapp_events(request: Request):
    try:
        raw_body = await request.body()
        data = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return {"status": "invalid_payload"}

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                for msg in messages:
                    action_detected = None
                    target_id_from_btn = None

                    # 1. Interactive Button Click
                    if msg.get("type") == "interactive":
                        btn_data = msg["interactive"].get("button_reply", {})
                        btn_id = btn_data.get("id", "").strip()
                        btn_title = btn_data.get("title", "").strip().lower()
                        print(f"📩 [Raw Button Hit] ID: '{btn_id}' | Title: '{btn_title}'")

                        if "PAY" in btn_id.upper() or "pay" in btn_title:
                            action_detected = "PAY"
                            target_id_from_btn = btn_id.replace("PAY_", "")
                        elif "OPT" in btn_id.upper() or "stop" in btn_title or "cancel" in btn_title:
                            action_detected = "OPT_OUT"
                            target_id_from_btn = btn_id.replace("OPT_OUT_", "")

                    # 2. Plain Text Reply (e.g., if user typed "Pay", "Done", "Stop")
                    elif msg.get("type") == "text":
                        txt = msg["text"].get("body", "").strip().lower()
                        print(f"💬 [Raw Text Hit] '{txt}'")
                        if any(w in txt for w in ["pay", "done", "ok", "yes"]):
                            action_detected = "PAY"
                        elif any(w in txt for w in ["stop", "cancel", "opt", "no"]):
                            action_detected = "OPT_OUT"

                    # 3. Resolve Target Transaction in SQLite
                    if action_detected:
                        conn = get_db()
                        cursor = conn.cursor()

                        # If button provided a valid ID, use it; otherwise pick latest pending transaction
                        if target_id_from_btn and target_id_from_btn.startswith("TXN_"):
                            cursor.execute("SELECT id, amount_inr FROM transactions WHERE id = ?", (target_id_from_btn,))
                        else:
                            cursor.execute("SELECT id, amount_inr FROM transactions WHERE status = 'PENDING_RETRY' ORDER BY created_at DESC LIMIT 1")
                        
                        row = cursor.fetchone()
                        conn.close()

                        if row:
                            txn_id = row["id"]
                            amt = row["amount_inr"]

                            if action_detected == "PAY":
                                print(f"🔥 [SUCCESS] Finalizing {txn_id} as RECOVERED (₹{amt})")
                                finalize_transaction(
                                    txn_id, "RECOVERED", amt,
                                    f"💳 [{datetime.now().strftime('%H:%M:%S')}] User Tap Verified on WhatsApp. Settled via Razorpay 1-Click FastPay."
                                )
                            elif action_detected == "OPT_OUT":
                                print(f"🛑 [TERMINATED] Finalizing {txn_id} as OPT-OUT")
                                finalize_transaction(
                                    txn_id, "TERMINATED", 0.0,
                                    f"🛑 [{datetime.now().strftime('%H:%M:%S')}] User Selected 'Stop / Cancel' on WhatsApp. Recovery Terminated."
                                )
                        else:
                            print("⚠️ No pending transaction found in ledger to update.")

    except Exception as e:
        print(f"❌ Webhook parser error: {e}")

    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)