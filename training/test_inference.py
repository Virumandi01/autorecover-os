import os
import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"
ADAPTER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "lora_adapter"))

# 1. Load 4-bit Base Model
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=bnb_config,
    device_map="auto"
)
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)

# 2. Build Messages
messages = [
    {
        "role": "system",
        "content": "You are Razorpay AI Recovery Engine. Analyze the failed transaction and output strictly structured recovery JSON with root-cause analysis and localized customer messaging."
    },
    {
        "role": "user",
        "content": "Txn: TXN_9999, Cust: Vikram Malhotra, Amt: ₹12500, Cat: CHECKOUT_DROPOFF, Reason: OTP_DROPOFF"
    }
]

# 3. Format using Qwen2.5 Chat Template
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.1,
        do_sample=False
    )

response_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

print("=" * 60)
print("⚡ LOCAL 3B MODEL RECOVERY DECISION (RTX 4060):")
print("=" * 60)
try:
    parsed = json.loads(response_text)
    print(json.dumps(parsed, indent=2))
except Exception:
    print(response_text)
print("=" * 60)