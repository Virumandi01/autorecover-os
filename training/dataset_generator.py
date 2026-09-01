import json
import random

CATEGORIES = ["PAYMENT_DEGRADATION", "CHECKOUT_DROPOFF", "FAILED_SUBSCRIPTION", "B2B_RECEIVABLES", "MANDATE_RETRY"]
NAMES = ["Aarav Sharma", "Priya Patel", "Vikram Malhotra", "Ananya Iyer", "Rohit Verma", "Nexus Retail Ltd", "Apex Tech Solutions"]

SYSTEM_PROMPT = "You are Razorpay AI Recovery Engine. Analyze the failed transaction and output strictly structured recovery JSON with root-cause analysis and localized customer messaging."

def generate_samples(count=250):
    dataset = []
    
    for i in range(count):
        cat = random.choice(CATEGORIES)
        name = random.choice(NAMES)
        amount = round(random.uniform(500, 75000), 2)
        txn_id = f"TXN_{3000 + i}"
        
        if cat == "CHECKOUT_DROPOFF":
            user_msg = f"Txn: {txn_id}, Cust: {name}, Amt: ₹{amount}, Cat: CHECKOUT_DROPOFF, Reason: OTP_DROPOFF"
            hinglish = f"Namaste {name}! Aapka ₹{amount:,.0f} ka payment complete nahi ho paya. 1-click me yahan se complete karein: https://rzp.io/l/{txn_id.lower()}"
            assistant_resp = {
                "category": "CHECKOUT_DROPOFF",
                "primary_action": "WHATSAPP_FAST_PAY",
                "delay_minutes": 5,
                "root_cause": "High-intent OTP drop-off. Dispatched instant WhatsApp 1-click checkout.",
                "hinglish_script": hinglish,
                "discount_pct": 3.0 if amount > 5000 else 0.0,
                "ptp_date": None
            }
        elif cat == "B2B_RECEIVABLES":
            days = random.randint(10, 40)
            user_msg = f"Txn: {txn_id}, Cust: {name}, Amt: ₹{amount}, Cat: B2B_RECEIVABLES, Reason: OVERDUE_INVOICE, OverdueDays: {days}"
            assistant_resp = {
                "category": "B2B_RECEIVABLES",
                "primary_action": "PTP_LOGGED" if days < 30 else "B2B_ESCALATION_EMAIL",
                "delay_minutes": 0,
                "root_cause": f"B2B invoice overdue by {days} days. Logged Promise-to-Pay timeline.",
                "hinglish_script": None,
                "discount_pct": 0.0,
                "ptp_date": "2026-09-15"
            }
        elif cat == "PAYMENT_DEGRADATION":
            user_msg = f"Txn: {txn_id}, Cust: {name}, Amt: ₹{amount}, Cat: PAYMENT_DEGRADATION, Reason: BANK_DOWNTIME"
            assistant_resp = {
                "category": "PAYMENT_DEGRADATION",
                "primary_action": "SILENT_MANDATE_RETRY",
                "delay_minutes": 90,
                "root_cause": "Issuer bank degradation. Scheduled silent retry after node clearance.",
                "hinglish_script": None,
                "discount_pct": 0.0,
                "ptp_date": None
            }
        elif cat == "MANDATE_RETRY":
            user_msg = f"Txn: {txn_id}, Cust: {name}, Amt: ₹{amount}, Cat: MANDATE_RETRY, Reason: INSUFFICIENT_FUNDS"
            assistant_resp = {
                "category": "MANDATE_RETRY",
                "primary_action": "SILENT_MANDATE_RETRY",
                "delay_minutes": 360,
                "root_cause": "Mandate paused for salary account top-up. Re-queued inside NPCI 8AM-8PM window.",
                "hinglish_script": None,
                "discount_pct": 0.0,
                "ptp_date": None
            }
        else: # FAILED_SUBSCRIPTION
            user_msg = f"Txn: {txn_id}, Cust: {name}, Amt: ₹{amount}, Cat: FAILED_SUBSCRIPTION, Reason: EXPIRED_CARD"
            hinglish = f"Namaste {name}, aapka subscription renew nahi ho paya kyonki card invalid ho gaya hai. Yahan update karein: https://rzp.io/s/{txn_id.lower()}"
            assistant_resp = {
                "category": "FAILED_SUBSCRIPTION",
                "primary_action": "HINGLISH_VOICE_NUDGE",
                "delay_minutes": 30,
                "root_cause": "Card token expired. Triggered dunning update notification.",
                "hinglish_script": hinglish,
                "discount_pct": 0.0,
                "ptp_date": None
            }
        
        sample = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": json.dumps(assistant_resp)}
            ]
        }
        dataset.append(sample)

    with open("training/dataset.jsonl", "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item) + "\n")

    print(f"✅ Generated {count} high-quality training pairs in training/dataset.jsonl")

if __name__ == "__main__":
    generate_samples(250)