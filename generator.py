import random
from typing import List
from schemas import PaymentEvent, RecoveryCategory, FailureReason

def generate_full_scenario_events(count: int = 50) -> List[PaymentEvent]:
    categories = list(RecoveryCategory)
    names = [
        "Aarav Sharma", "Priya Patel", "Vikram Malhotra", 
        "Ananya Iyer", "Rohit Verma", "TechCorp Pvt Ltd", "Nexus Retail Ltd"
    ]
    events = []

    for i in range(1, count + 1):
        cat = random.choice(categories)
        cust_name = random.choice(names)
        retry_cnt = random.randint(0, 4)
        opt_out = True if retry_cnt >= 3 and random.random() > 0.7 else False

        if cat == RecoveryCategory.PAYMENT_DEGRADATION:
            reason = random.choice([FailureReason.BANK_DOWNTIME, FailureReason.PACKET_LOSS])
            amount = round(random.uniform(500, 8000), 2)
            channel = "UPI"
            overdue = 0
        elif cat == RecoveryCategory.CHECKOUT_DROPOFF:
            reason = FailureReason.OTP_DROPOFF
            amount = round(random.uniform(1200, 15000), 2)
            channel = "CARD"
            overdue = 0
        elif cat == RecoveryCategory.FAILED_SUBSCRIPTION:
            reason = random.choice([FailureReason.EXPIRED_CARD, FailureReason.INSUFFICIENT_FUNDS])
            amount = round(random.uniform(499, 3999), 2)
            channel = "CARD_AUTOPAY"
            overdue = random.randint(1, 5)
        elif cat == RecoveryCategory.MANDATE_RETRY:
            reason = random.choice([FailureReason.INSUFFICIENT_FUNDS, FailureReason.MANDATE_REJECTED])
            amount = round(random.uniform(2000, 25000), 2)
            channel = "UPI_MANDATE"
            overdue = 0
        else:  # B2B_RECEIVABLES
            reason = FailureReason.OVERDUE_INVOICE
            amount = round(random.uniform(25000, 150000), 2)
            channel = "NETBANKING_INVOICE"
            overdue = random.randint(5, 45)

        events.append(
            PaymentEvent(
                transaction_id=f"TXN_{2000 + i}",
                customer_id=f"CUST_{800 + i}",
                customer_name=cust_name,
                category=cat,
                amount_inr=amount,
                channel=channel,
                failure_reason=reason,
                retry_count=retry_cnt,
                days_overdue=overdue,
                is_salary_account=(reason == FailureReason.INSUFFICIENT_FUNDS and random.random() > 0.4),
                customer_opt_out=opt_out,
                promised_pay_date="2026-09-08" if cat == RecoveryCategory.B2B_RECEIVABLES and overdue > 15 else None
            )
        )
    return events

# Backwards compatibility alias
generate_mock_events = generate_full_scenario_events

if __name__ == "__main__":
    batch = generate_full_scenario_events(5)
    for b in batch:
        print(b.model_dump_json(indent=2))