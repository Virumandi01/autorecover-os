import time
import random
from datetime import datetime
from db import init_db, insert_transaction
from schemas import RecoveryCategory, FailureReason

NAMES = [
    "Aarav Sharma", 
    "Priya Patel", 
    "Vikram Malhotra", 
    "Ananya Iyer", 
    "Rohit Verma", 
    "Nexus Retail Ltd", 
    "Apex Tech Solutions"
]
CATEGORIES = list(RecoveryCategory)
CHANNELS = ["UPI", "CARD", "NETBANKING", "UPI_MANDATE"]

def generate_single_event(custom_status: str = None) -> dict:
    txn_id = f"TXN_{random.randint(10000, 99999)}"
    name = random.choice(NAMES)
    amount = round(random.uniform(499.0, 35000.0), 2)
    cat = random.choice(CATEGORIES)
    channel = random.choice(CHANNELS)
    
    is_failed = custom_status == "FAILED" or (custom_status is None and random.random() < 0.85)
    
    status = "PENDING_RETRY" if is_failed else "SUCCESS"
    reason = None
    days_overdue = 0
    if is_failed:
        reason = random.choice(list(FailureReason)).value
        if cat == RecoveryCategory.B2B_RECEIVABLES:
            days_overdue = random.randint(5, 45)
            amount = round(random.uniform(25000.0, 120000.0), 2)

    return {
        "id": txn_id,
        "customer_name": name,
        "customer_phone": f"+9198{random.randint(10000000, 99999999)}",
        "category": cat.value,
        "amount_inr": amount,
        "channel": channel,
        "status": status,
        "failure_reason": reason,
        "days_overdue": days_overdue,
        "is_salary_account": random.random() > 0.5,
        "customer_opt_out": random.random() > 0.90,
        "promised_pay_date": "2026-09-10" if days_overdue > 15 else None
    }

def main():
    init_db()
    print("=" * 60)
    print("📡 LIVE REAL-TIME GATEWAY EMITTER")
    print("  [1] Emit 1 transaction (Triggers live delayed workflow)")
    print("  [2] Burst stream 10 failed transactions")
    print("  [3] Continuous stream (1 every 4 seconds)")
    print("=" * 60)

    while True:
        choice = input("\nEnter Choice (1 / 2 / 3 / q): ").strip()
        if choice == "1":
            event = generate_single_event()
            insert_transaction(event)
            print(f"⚡ Emitted: {event['id']} | ₹{event['amount_inr']} | Status: {event['status']} ({event.get('failure_reason')})")
        elif choice == "2":
            for _ in range(10):
                insert_transaction(generate_single_event("FAILED"))
            print("✅ Injected 10 failed payments awaiting scheduled temporal recovery.")
        elif choice == "3":
            print("🌊 Continuous streaming active (Ctrl + C to stop)...")
            try:
                while True:
                    event = generate_single_event()
                    insert_transaction(event)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Emitted {event['id']} -> {event['status']}")
                    time.sleep(4)
            except KeyboardInterrupt:
                print("\nStream paused.")
                break
        elif choice.lower() == "q":
            break


if __name__ == "__main__":
    main()