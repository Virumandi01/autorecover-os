import os
import json
import torch
import config
from schemas import PaymentEvent, WorkflowDecision, WorkflowStep, ActionType

# Check if Local GPU Adapter exists
ADAPTER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "training", "lora_adapter"))
LOCAL_MODEL_READY = os.path.exists(os.path.join(ADAPTER_PATH, "adapter_config.json"))

_local_model = None
_local_tokenizer = None

def get_local_model():
    """Lazy-loads local 3B model onto RTX 4060."""
    global _local_model, _local_tokenizer
    if _local_model is None and LOCAL_MODEL_READY:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            from peft import PeftModel

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
            base_model_id = "Qwen/Qwen2.5-3B-Instruct"
            _local_tokenizer = AutoTokenizer.from_pretrained(base_model_id)
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                quantization_config=bnb_config,
                device_map="auto"
            )
            _local_model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
        except Exception as e:
            print(f"[Local SLM Warning] GPU Model loading skipped: {e}")
            _local_model = None
    return _local_model, _local_tokenizer

def generate_hinglish_voice_script(*args, **kwargs) -> str:
    """
    Polymorphic signature: accepts either (event) or (customer_name, amount, link/reason).
    """
    if len(args) == 1 and isinstance(args[0], PaymentEvent):
        ev = args[0]
        cust = ev.customer_name
        amt = ev.amount_inr
        tid = ev.transaction_id
    elif len(args) >= 2:
        cust = str(args[0])
        amt = args[1]
        tid = "quick_pay"
    else:
        cust = kwargs.get("customer_name", "Customer")
        amt = kwargs.get("amount", 0.0)
        tid = "quick_pay"

    return f"Namaste {cust}! Aapka ₹{amt:,.0f} ka payment pending hai. Yahan 1-click me complete karein: https://rzp.io/l/{str(tid).lower()}"

def query_local_slm(event: PaymentEvent) -> dict:
    """Runs local inference on RTX 4060 with 0 API cost."""
    model, tokenizer = get_local_model()
    if model is None:
        raise RuntimeError("Local GPU model not loaded")

    user_msg = f"Txn: {event.transaction_id}, Cust: {event.customer_name}, Amt: ₹{event.amount_inr}, Cat: {event.category.value}, Reason: {event.failure_reason.value}"
    messages = [
        {"role": "system", "content": "You are Razorpay AI Recovery Engine. Analyze the failed transaction and output strictly structured recovery JSON with root-cause analysis and localized customer messaging."},
        {"role": "user", "content": user_msg}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.1, do_sample=False)
    
    raw = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return json.loads(raw)

def diagnose_and_decide(event: PaymentEvent) -> WorkflowDecision:
    # 1. Try Local Dedicated SLM on RTX 4060
    if LOCAL_MODEL_READY:
        try:
            raw = query_local_slm(event)
            action = ActionType(raw.get("primary_action", "WHATSAPP_FAST_PAY"))
            delay = raw.get("delay_minutes", 5)
            return WorkflowDecision(
                category=event.category,
                primary_action=action,
                workflow_steps=[
                    WorkflowStep(
                        step_number=1,
                        scheduled_delay_minutes=delay,
                        action=action,
                        channel=event.channel,
                        reason_context=raw.get("root_cause", "Processed by Local SLM.")
                    )
                ],
                root_cause_diagnosis=raw.get("root_cause", "Local SLM Diagnosis."),
                hinglish_script=raw.get("hinglish_script") or generate_hinglish_voice_script(event),
                discount_percentage=raw.get("discount_pct", 0.0),
                promise_to_pay_date=raw.get("ptp_date")
            )
        except Exception as e:
            print(f"[AutoRecover SLM Fallback] Local inference failover triggered: {e}")

    # 2. Cloud Fallback using google-genai
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        prompt = f"Diagnose payment failure: ID={event.transaction_id}, Amt={event.amount_inr}, Reason={event.failure_reason.value}, Customer={event.customer_name}"
        response = client.models.generate_content(
            model=config.DEFAULT_MODEL,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=WorkflowDecision,
                temperature=0.1
            )
        )
        return WorkflowDecision.model_validate_json(response.text)
    except Exception:
        # 3. Deterministic Code Failsafe
        return WorkflowDecision(
            category=event.category,
            primary_action=ActionType.WHATSAPP_FAST_PAY,
            workflow_steps=[
                WorkflowStep(
                    step_number=1,
                    scheduled_delay_minutes=5,
                    action=ActionType.WHATSAPP_FAST_PAY,
                    channel="WHATSAPP",
                    reason_context="Deterministic recovery fallback."
                )
            ],
            root_cause_diagnosis="Resolved via deterministic engine failsafe.",
            hinglish_script=generate_hinglish_voice_script(event)
        )