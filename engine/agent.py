import json
from google import genai
from google.genai import types
import config
from schemas import PaymentEvent, AgentDecision, ActionType

client = genai.Client(api_key=config.GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are the AI Recovery Diagnostics Engine for an Indian Payment Gateway.
Your goal is to determine the optimal recovery strategy for failed payments and dropouts.

Rules:
1. INSUFFICIENT_FUNDS on salary accounts: Schedule a retry for 24-48 hours (wait for salary/balance top-up).
2. OTP_TIMEOUT / USER_ABANDONED: High intent drop-off. Send immediate WhatsApp 1-click payment link.
3. Over INR 5000 drop-offs: You may offer up to 5% incentive discount to close the recovery immediately.
4. Output ONLY valid structured data matching the schema. Keep rationale strictly under 15 words.
"""

def diagnose_and_decide(event: PaymentEvent) -> AgentDecision:
    """Invokes Gemini with structured JSON output schema."""
    user_content = f"""
    Evaluate this failed payment event:
    - ID: {event.transaction_id}
    - Amount: INR {event.amount_inr}
    - Channel: {event.channel.value}
    - Failure Reason: {event.failure_reason.value}
    - Retry Count: {event.retry_count}
    - Is Salary Account: {event.is_salary_account}
    """

    try:
        response = client.models.generate_content(
            model=config.DEFAULT_MODEL,
            contents=[
                types.Content(role="user", parts=[types.Part.from_text(text=user_content)])
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=AgentDecision,
                temperature=0.1
            )
        )
        # Parse directly from structured JSON
        decision = AgentDecision.model_validate_json(response.text)
        return decision
    except Exception as e:
        # Failsafe deterministic fallback
        return AgentDecision(
            action=ActionType.WHATSAPP_PAY_LINK,
            target_channel="WHATSAPP",
            scheduled_hour_delay=0,
            rationale=f"Failsafe triggered due to agent timeout: {str(e)[:30]}",
            incentive_discount_pct=0.0
        )