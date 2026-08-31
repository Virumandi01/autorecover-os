import random
from typing import List
from schemas import PaymentEvent, PaymentChannel, FailureReason

def generate_mock_events(count: int = 50) -> List[PaymentEvent]:
    reasons = list(FailureReason)
    channels = list(PaymentChannel)
    
    events = []
    for i in range(1, count + 1):
        reason = random.choice(reasons)
        channel = random.choice(channels)
        
        # Realistic business rules for synthetic context
        is_salary = reason == FailureReason.INSUFFICIENT_FUNDS and random.random() > 0.4
        retry_count = random.randint(0, 4)
        opt_out = True if retry_count >= 3 and random.random() > 0.7 else False

        events.append(
            PaymentEvent(
                transaction_id=f"txn_{1000 + i}",
                customer_id=f"cust_{500 + i}",
                customer_name=f"Customer {i}",
                amount_inr=round(random.uniform(499.0, 15000.0), 2),
                channel=channel,
                failure_reason=reason,
                retry_count=retry_count,
                is_salary_account=is_salary,
                customer_opt_out=opt_out
            )
        )
    return events

if __name__ == "__main__":
    batch = generate_mock_events(5)
    for b in batch:
        print(b.model_dump_json(indent=2))