import time
import random
from datetime import datetime
from db import init_db, insert_transaction
from schemas import RecoveryCategory, FailureReason

NAMES = ["Aarav Sharma", "Priya Patel", "Vikram Malhotra", "Ananya Iyer", "Rohit Verma", "TechCorp India", "Nexus Retail Ltd"]
CATEGORIES = list(RecoveryCategory)
CHANNELS = ["UPI", "CARD", "NETBANKING", "UPI_MANDATE"]

def generate_single_event(custom_status: str = None, custom_reason: FailureReason = None) -> dict:
    txn_id = f"TXN_{random.randint(10000, 99999)}"
    name = random.choice(NAMES)
    amount = round(random.uniform(499.0, 25000.0), 2)
    cat = random.choice(CATEGORIES)
    channel = random.choice(CHANNELS)
    
    # 80% chance of failure if not specified, to test recovery
    status = custom_status or ("SUCCESS" if random.random() < 0.20 else "FAILED")
    
    reason = None
    days_overdue = 0
    if status == "FAILED":
        reason = custom_reason.value if custom_reason else random.choice(list(FailureReason)).value
        if cat == RecoveryCategory.B2B_RECEIVABLES:
            days_overdue = random.randint(5, 45)
            amount = round(random.uniform(25000.0, 120000.0), 2)

    return {
        "id": txn_id,
        "customer_name": name,
        "category": cat.value,
        "amount_inr": amount,
        "channel": channel,
        "status": status,
        "failure_reason": reason,
        "retry_count": random.randint(0, 3),
        "days_overdue": days_overdue,
        "is_salary_account": random.random() > 0.5,
        "customer_opt_out": random.random() > 0.85,
        "promised_pay_date": "2026-09-10" if days_overdue > 15 else None
    }

def main():
    init_db()
    print("=" * 60)
    print("📡 LIVE PAYMENT EVENT STREAMER STARTED")
    print("Commands:")
    print("  [1] Emit a single random transaction")
    print("  [2] Burst stream 50 transactions at once")
    print("  [3] Continuously stream 1 transaction every 3 seconds")
    print("=" * 60)

    while True:
        choice = input("\nEnter Choice (1 / 2 / 3 / q): ").strip()
        if choice == "1":
            event = generate_single_event()
            insert_transaction(event)
            print(f"⚡ Emitted: {event['id']} | ₹{event['amount_inr']} | {event['status']} | {event.get('failure_reason')}")
        elif choice == "2":
            print("🚀 Emitting burst of 50 transactions...")
            for _ in range(50):
                event = generate_single_event()
                insert_transaction(event)
            print("✅ 50 transactions injected into recovery_ledger.db!")
        elif choice == "3":
            print("🌊 Continuous streaming active (Ctrl + C to stop)...")
            try:
                while True:
                    event = generate_single_event()
                    insert_transaction(event)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Emitted {event['id']} -> {event['status']} ({event.get('failure_reason')})")
                    time.sleep(3)
            except KeyboardInterrupt:
                print("\nStream paused.")
        elif choice.lower() == "q":
            break

if __name__ == "__main__":
    main()