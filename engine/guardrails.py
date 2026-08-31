import config
from schemas import PaymentEvent, AgentDecision, ActionType

class GuardrailViolation(Exception):
    pass

def apply_guardrails(event: PaymentEvent, decision: AgentDecision) -> AgentDecision:
    """
    Validates agent outputs against strict regulatory and financial boundaries.
    Mutates or caps the decision if it breaches business bounds.
    """
    # Guardrail 1: Stopping Rule (Hard Cap on Retries)
    if event.retry_count >= config.MAX_RETRIES_ALLOWED:
        decision.action = ActionType.TERMINATE
        decision.rationale = "[Guardrail Intercept] Max retries reached. Action suppressed."
        decision.incentive_discount_pct = 0.0
        return decision

    # Guardrail 2: Hard Cap on Financial Incentives
    if decision.incentive_discount_pct > config.MAX_DISCOUNT_PERCENT:
        decision.incentive_discount_pct = config.MAX_DISCOUNT_PERCENT
        decision.rationale += " [Guardrail Intercept: Discount capped at 5%]"

    # Guardrail 3: Opt-out Compliance
    if event.customer_opt_out:
        decision.action = ActionType.TERMINATE
        decision.rationale = "[Guardrail Intercept] Customer opt-out active. Termination enforced."
        decision.incentive_discount_pct = 0.0

    return decision