import os
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig
from trl import SFTTrainer

MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "lora_adapter"))

def format_prompts(batch):
    formatted_texts = []
    for messages in batch["messages"]:
        text = f"<|im_start|>system\n{messages[0]['content']}<|im_end|>\n"
        text += f"<|im_start|>user\n{messages[1]['content']}<|im_end|>\n"
        text += f"<|im_start|>assistant\n{messages[2]['content']}<|im_end|>"
        formatted_texts.append(text)
    return {"text": formatted_texts}

def main():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. Please check your GPU driver.")

    print(f"🚀 Initializing QLoRA Fine-Tuning on: {torch.cuda.get_device_name(0)}")

    # 1. 4-bit Quantization Config for RTX 4060
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # 2. Tokenizer & Base Model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto"
    )

    # 3. LoRA Configuration
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )

    # 4. Load & Format Dataset
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dataset.jsonl"))
    dataset = load_dataset("json", data_files=dataset_path, split="train")
    dataset = dataset.map(format_prompts, batched=True)

    # 5. Windows-Compatible Training Arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        num_train_epochs=3,
        logging_steps=5,
        fp16=True,
        optim="adamw_torch",        # Stable on Windows (no paged deadlocks)
        save_strategy="no",         # Saves once at the very end to prevent mid-training I/O lock
        report_to="none"
    )

    # 6. SFTTrainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=512,
        peft_config=peft_config,
        tokenizer=tokenizer,
        args=training_args,
    )

    print("⚡ Starting Training...")
    trainer.train()

    print("💾 Saving LoRA adapter weights...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"✅ Training completed! Weights saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()