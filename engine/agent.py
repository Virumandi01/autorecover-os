from google import genai
from google.genai import types
import config
from schemas import PaymentEvent, WorkflowDecision, WorkflowStep, ActionType

client = genai.Client(api_key=config.GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are Razorpay's AI Revenue Recovery Engine.
Generate deterministic recovery decisions and natural, respectful Hinglish recovery scripts when required.

Capabilities:
1. For drop-offs / failed subscriptions: create clear Hinglish communication scripts (e.g. "Namaste [Name], aapka ₹[Amount] ka payment pause ho gaya hai. Yahan click karke 10 second me complete karein").
2. For B2B receivables: determine if a Promise-to-Pay (PTP) should be logged or escalated to legal/finance notices based on days overdue.
3. Keep recovery incentive discount <= 5%.
"""

def generate_hinglish_voice_script(customer_name: str, amount: float, link: str) -> str:
    """Generates concise Hinglish voice/WhatsApp prompt."""
    return f"Namaste {customer_name}! Aapka ₹{amount:,.0f} ka Razorpay transaction complete nahi ho paya. Dobara bina kisi rukawat ke pay karne ke liye ye link use karein: {link}"

def run_ai_diagnostics(event: PaymentEvent) -> WorkflowDecision:
    """Invokes Gemini for complex unstructured recovery decisions."""
    try:
        user_prompt = f"""
        Diagnose transaction:
        - Customer: {event.customer_name}
        - Category: {event.category.value}
        - Amount: INR {event.amount_inr}
        - Reason: {event.failure_reason.value}
        - Overdue Days: {event.days_overdue}
        - Retry Count: {event.retry_count}
        """

        response = client.models.generate_content(
            model=config.DEFAULT_MODEL,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=WorkflowDecision,
                temperature=0.1
            )
        )
        return WorkflowDecision.model_validate_json(response.text)
    except Exception:
        # Failsafe deterministic fallback
        script = generate_hinglish_voice_script(event.customer_name, event.amount_inr, "https://rzp.io/i/rec_xyz")
        return WorkflowDecision(
            category=event.category,
            primary_action=ActionType.HINGLISH_VOICE_NUDGE,
            workflow_steps=[
                WorkflowStep(
                    step_number=1,
                    scheduled_delay_minutes=15,
                    action=ActionType.HINGLISH_VOICE_NUDGE,
                    channel="WHATSAPP_VOICE",
                    message_content=script,
                    reason_context="Failsafe Hinglish reminder dispatched."
                )
            ],
            root_cause_diagnosis=f"Recovering {event.category.value} via localized nudge.",
            hinglish_script=script,
            recovery_incentive_pct=0.0
        )