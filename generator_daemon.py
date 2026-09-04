import time
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from db import init_db, insert_transaction, clear_all_transactions
from schemas import RecoveryCategory, FailureReason

load_dotenv(override=True)
TARGET_PHONE = os.getenv("TARGET_TEST_PHONE", "+919876543210")

CUST_NAMES = [
    "Aarav Sharma", "Priya Patel", "Vikram Malhotra", "Ananya Iyer", "Rohit Verma",
    "Nexus Retail Ltd", "Apex Tech Solutions", "Kavita Rao", "Aditya Joshi", "Siddharth Sen",
    "Meera Nair", "Rajesh Kumar", "Divya Menon", "Rohan Gupta", "Deepak Verma"
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
    """Emits exactly 1 transaction for testing."""
    init_db()
    t_id = f"TXN_{random.randint(40000, 99999)}"
    amt = round(random.uniform(1500.0, 18000.0), 2)
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
    print(f"⚡ [Emitted 1 Event] {t_id} for Harisankar S (₹{amt}) -> Target WhatsApp: {TARGET_PHONE}")

def generate_benchmark_50():
    """Generates 50 structured benchmark transactions (30 Success, 15 Recovery, 5 Terminated)."""
    init_db()
    clear_all_transactions()
    base_time = datetime.now() - timedelta(minutes=150)
    txns = []

    # 1. 30 Pure Success Transactions
    for i in range(1, 31):
        t_time = base_time + timedelta(minutes=i * 2)
        amt = round(random.uniform(500.0, 15000.0), 2)
        cat = random.choice(CATEGORIES)
        ch = random.choice(["UPI", "CARD", "NETBANKING"])
        cust = random.choice(CUST_NAMES)
        txns.append({
            "id": f"TXN_{10000 + i}",
            "customer_name": cust,
            "customer_phone": "+919800000000",
            "category": cat.value,
            "amount_inr": amt,
            "channel": ch,
            "status": "SUCCESS",
            "failure_reason": None,
            "days_overdue": 0,
            "is_salary_account": False,
            "customer_opt_out": False,
            "promised_pay_date": None,
            "created_at": t_time.isoformat()
        })

    # 2. 15 Multi-Step Error-Recovered Transactions
    recovery_scenarios = [
        ("CHECKOUT_DROPOFF", FailureReason.PACKET_LOSS, "WHATSAPP_FAST_PAY"),
        ("MANDATE_RETRY", FailureReason.INSUFFICIENT_FUNDS, "SILENT_MANDATE_RETRY"),
        ("FAILED_SUBSCRIPTION", FailureReason.EXPIRED_CARD, "HINGLISH_VOICE_NUDGE"),
        ("PAYMENT_DEGRADATION", FailureReason.BANK_DOWNTIME, "SILENT_MANDATE_RETRY"),
        ("B2B_RECEIVABLES", FailureReason.EXPIRED_CARD, "B2B_ESCALATION_EMAIL")
    ]

    for j in range(1, 16):
        t_time = base_time + timedelta(minutes=60 + j * 3)
        amt = round(random.uniform(2500.0, 48000.0), 2)
        cat_str, f_reason, action = random.choice(recovery_scenarios)
        cust = CUST_NAMES[j % len(CUST_NAMES)]
        cust_phone = TARGET_PHONE if j == 1 else f"+9198{random.randint(10000000, 99999999)}"
        
        txns.append({
            "id": f"TXN_{20000 + j}",
            "customer_name": cust,
            "customer_phone": cust_phone,
            "category": cat_str,
            "amount_inr": amt,
            "channel": "UPI" if "DROPOFF" in cat_str else "UPI_MANDATE",
            "status": "PENDING_RETRY",
            "failure_reason": f_reason.value,
            "days_overdue": random.randint(10, 35) if cat_str == "B2B_RECEIVABLES" else 0,
            "is_salary_account": True if j % 2 == 0 else False,
            "customer_opt_out": False,
            "promised_pay_date": "2026-09-12" if cat_str == "B2B_RECEIVABLES" else None,
            "created_at": t_time.isoformat()
        })

    # 3. 5 Terminated / Lost Revenue Transactions
    for k in range(1, 6):
        t_time = base_time + timedelta(minutes=110 + k * 2)
        amt = round(random.uniform(8000.0, 85000.0), 2)
        cat = random.choice(CATEGORIES)
        f_reason = random.choice(FAILURE_POOL)
        cust = random.choice(["Apex Tech Solutions", "Nexus Retail Ltd", "Vikram Malhotra"])
        
        txns.append({
            "id": f"TXN_{30000 + k}",
            "customer_name": cust,
            "customer_phone": f"+9198{random.randint(10000000, 99999999)}",
            "category": cat.value,
            "amount_inr": amt,
            "channel": "CARD",
            "status": "PENDING_RETRY",
            "failure_reason": f_reason.value,
            "days_overdue": 45 if cat == RecoveryCategory.B2B_RECEIVABLES else 0,
            "is_salary_account": False,
            "customer_opt_out": (k == 5),
            "promised_pay_date": None,
            "created_at": t_time.isoformat()
        })

    for item in txns:
        insert_transaction(item)
    print(f"✅ [Seeded 50 Transactions] 30 Success, 15 Scheduled Recovery, 5 Final Terminated.")

def main():
    init_db()
    print("=" * 60)
    print("📡 LIVE GATEWAY BENCHMARK & TEST CONTROLLER")
    print("  [1] Emit 1 single live test event (Routes to verified WhatsApp)")
    print("  [2] Seed Benchmark 50 Dataset (30 Success, 15 Recovery, 5 Terminated)")
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