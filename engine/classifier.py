from typing import Optional
from schemas import PaymentEvent, AgentDecision, ActionType, FailureReason

def rule_based_triage(event: PaymentEvent) -> Optional[AgentDecision]:
    """
    Evaluates hard mechanical rules with zero token overhead.
    Returns an AgentDecision if resolved deterministically, else None (routes to LLM).
    """
    # Hard Stopping Rule: Opted out or max attempts exceeded
    if event.customer_opt_out or event.retry_count >= 3:
        return AgentDecision(
            action=ActionType.TERMINATE,
            target_channel="NONE",
            scheduled_hour_delay=0,
            rationale="Max retry limit reached or customer opted out."
        )

    # Bank Downtime -> Silent Retry during next operational window
    if event.failure_reason == FailureReason.BANK_DOWNTIME:
        return AgentDecision(
            action=ActionType.SILENT_RETRY,
            target_channel="API_MANDATE",
            scheduled_hour_delay=4,
            rationale="Issuer bank degradation detected. Queued silent retry."
        )

    # Expired card -> Needs alternate checkout link
    if event.failure_reason == FailureReason.EXPIRED_CARD:
        return AgentDecision(
            action=ActionType.WHATSAPP_PAY_LINK,
            target_channel="WHATSAPP",
            scheduled_hour_delay=0,
            rationale="Card expired. Sent dynamic update link to customer."
        )

    # Pass nuanced drop-offs (Insufficient funds, OTP dropouts) to LLM agent
    return None