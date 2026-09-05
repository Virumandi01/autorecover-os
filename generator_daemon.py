import time
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(override=True)

from db import init_db, insert_transaction, clear_all_transactions
from schemas import RecoveryCategory, FailureReason
from engine.dispatcher import synthesize_hinglish_voice, send_real_whatsapp_interactive

TARGET_PHONE = os.getenv("TARGET_TEST_PHONE", "916381121659")

CUST_NAMES = [
    "Aarav Sharma", "Priya Patel", "Vikram Malhotra", "Ananya Iyer", "Rohit Verma",
    "Nexus Retail Ltd", "Apex Tech Solutions", "Kavita Rao", "Aditya Joshi", "Siddharth Sen"
]

CATEGORIES = list(RecoveryCategory)
FAILURE_POOL = [
    FailureReason.BANK_DOWNTIME,
    FailureReason.INSUFFICIENT_FUNDS,
    FailureReason.EXPIRED_CARD,
    FailureReason.MANDATE_REJECTED,
    FailureReason.PACKET_LOSS
]

def emit_single_live_transaction():
    """Emits 1 transaction, creates audio, and sends WhatsApp message."""
    init_db()
    t_id = f"TXN_{random.randint(40000, 99999)}"
    amt = round(random.uniform(2500.0, 18500.0), 2)
    hinglish_text = f"Namaste! Aapka payment network issue ki wajah se atak gaya tha. Niche button tap karke retry karein."

    print(f"\n⚡ Synthesizing Hinglish voice for {t_id}...")
    audio_path = synthesize_hinglish_voice(hinglish_text, t_id)

    # 1. Insert into Ledger
    ev = {
        "id": t_id,
        "customer_name": "Harisankar S",
        "customer_phone": TARGET_PHONE,
        "category": RecoveryCategory.CHECKOUT_DROPOFF.value,
        "amount_inr": amt,
        "channel": "UPI",
        "status": "PENDING_RETRY",
        "failure_reason": FailureReason.PACKET_LOSS.value,
        "days_overdue": 0,
        "is_salary_account": False,
        "customer_opt_out": False,
        "promised_pay_date": None
    }
    insert_transaction(ev)
    print(f"📝 Inserted {t_id} into database ledger.")

    # 2. Dispatch Outbound Message to WhatsApp
    print(f"📱 Dispatching WhatsApp message to {TARGET_PHONE}...")
    res = send_real_whatsapp_interactive(
        phone=TARGET_PHONE,
        customer_name="Harisankar S",
        amount=amt,
        pay_url=f"https://rzp.io/l/{t_id.lower()}",
        hinglish_text=hinglish_text,
        txn_id=t_id,
        send_voice=True
    )
    print(f"✅ Dispatch complete. System awaiting customer response.\n")

def generate_benchmark_50():
    """Generates 50 benchmark transactions (~26 Success, ~16 Recovery, ~8 Terminated)."""
    init_db()
    clear_all_transactions()
    base_time = datetime.now() - timedelta(minutes=150)
    txns = []

    # 1. 26 Direct Successes
    for i in range(1, 27):
        t_time = base_time + timedelta(minutes=i * 2)
        amt = round(random.uniform(800.0, 14500.0), 2)
        cat = random.choice(CATEGORIES)
        txns.append({
            "id": f"TXN_{10000 + i}",
            "customer_name": random.choice(CUST_NAMES),
            "customer_phone": "+919800000000",
            "category": cat.value,
            "amount_inr": amt,
            "channel": random.choice(["UPI", "CARD", "NETBANKING"]),
            "status": "SUCCESS",
            "failure_reason": None,
            "days_overdue": 0,
            "is_salary_account": False,
            "customer_opt_out": False,
            "promised_pay_date": None,
            "created_at": t_time.isoformat()
        })

    # 2. 16 Recoverable Errors
    error_matrix = [
        (RecoveryCategory.CHECKOUT_DROPOFF.value, FailureReason.PACKET_LOSS.value),
        (RecoveryCategory.MANDATE_RETRY.value, FailureReason.INSUFFICIENT_FUNDS.value),
        (RecoveryCategory.FAILED_SUBSCRIPTION.value, FailureReason.EXPIRED_CARD.value),
        (RecoveryCategory.PAYMENT_DEGRADATION.value, FailureReason.BANK_DOWNTIME.value),
        (RecoveryCategory.B2B_RECEIVABLES.value, FailureReason.MANDATE_REJECTED.value),
    ]
    for j in range(1, 17):
        t_time = base_time + timedelta(minutes=55 + j * 3)
        amt = round(random.uniform(3200.0, 42000.0), 2)
        cat_val, f_val = error_matrix[j % len(error_matrix)]
        txns.append({
            "id": f"TXN_{20000 + j}",
            "customer_name": CUST_NAMES[j % len(CUST_NAMES)],
            "customer_phone": f"+9198{random.randint(10000000, 99999999)}",
            "category": cat_val,
            "amount_inr": amt,
            "channel": "UPI" if "DROPOFF" in cat_val else "UPI_MANDATE",
            "status": "PENDING_RETRY",
            "failure_reason": f_val,
            "days_overdue": random.randint(12, 38) if cat_val == "B2B_RECEIVABLES" else 0,
            "is_salary_account": (j % 2 == 0),
            "customer_opt_out": False,
            "promised_pay_date": "2026-09-15" if cat_val == "B2B_RECEIVABLES" else None,
            "created_at": t_time.isoformat()
        })

    # 3. 8 Terminated Cases
    for k in range(1, 9):
        t_time = base_time + timedelta(minutes=105 + k * 2)
        amt = round(random.uniform(9500.0, 92000.0), 2)
        cat = random.choice(CATEGORIES)
        txns.append({
            "id": f"TXN_{30000 + k}",
            "customer_name": random.choice(["Apex Tech Solutions", "Nexus Retail Ltd", "Vikram Malhotra"]),
            "customer_phone": f"+9198{random.randint(10000000, 99999999)}",
            "category": cat.value,
            "amount_inr": amt,
            "channel": "CARD",
            "status": "PENDING_RETRY",
            "failure_reason": random.choice(FAILURE_POOL).value,
            "days_overdue": 50 if cat == RecoveryCategory.B2B_RECEIVABLES else 0,
            "is_salary_account": False,
            "customer_opt_out": (k >= 7),
            "promised_pay_date": None,
            "created_at": t_time.isoformat()
        })

    for item in txns:
        insert_transaction(item)
    print(f"✅ Ingested 50 benchmark transactions (~26 Success, ~16 Multi-Step Recovered, ~8 Terminated).")

def main():
    init_db()
    print("=" * 60)
    print("📡 LIVE GATEWAY BENCHMARK & DEMO CONTROLLER")
    print("  [1] Emit 1 single live interactive event (WhatsApp)")
    print("  [2] Seed Benchmark 50 Dataset")
    print("  [3] Clear entire database ledger")
    print("  [q] Quit")
    print("=" * 60)

    while True:
        c = input("\nEnter Choice (1/2/3/q): ").strip()
        if c == "1":
            emit_single_live_transaction()
        elif c == "2":
            generate_benchmark_50()
        elif c == "3":
            clear_all_transactions()
            print("🗑️ Database ledger cleared.")
        elif c.lower() == "q":
            break

if __name__ == "__main__":
    main()