import random
from schemas import PaymentEvent, AgentDecision, RecoveryResult, ActionType

def execute_recovery(event: PaymentEvent, decision: AgentDecision) -> RecoveryResult:
    """
    Executes bounded action via simulated Razorpay API / Communication webhook.
    """
    if decision.action == ActionType.TERMINATE:
        return RecoveryResult(
            transaction_id=event.transaction_id,
            initial_amount=event.amount_inr,
            action_taken=decision.action,
            recovered=False,
            amount_recovered=0.0,
            audit_note=f"Terminated: {decision.rationale}"
        )

    # Realistic recovery probability based on intervention type
    success_probability = 0.85 if decision.action == ActionType.WHATSAPP_PAY_LINK else 0.70
    is_success = random.random() < success_probability

    if is_success:
        discount_factor = 1.0 - (decision.incentive_discount_pct / 100.0)
        recovered_amount = round(event.amount_inr * discount_factor, 2)
        audit = f"Recovered via {decision.target_channel}. Delay: {decision.scheduled_hour_delay}h. Discount: {decision.incentive_discount_pct}%"
    else:
        recovered_amount = 0.0
        audit = f"Failed after execution on {decision.target_channel}."

    return RecoveryResult(
        transaction_id=event.transaction_id,
        initial_amount=event.amount_inr,
        action_taken=decision.action,
        recovered=is_success,
        amount_recovered=recovered_amount,
        audit_note=audit
    )