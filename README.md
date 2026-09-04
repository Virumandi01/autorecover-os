#  AutoRecover OS: Autonomous AI-Driven Payment Recovery Engine

> **Razorpay AI Builder Buildathon | Track 03: AI Revenue Recovery & Dunning Engine**  
> *Autonomous, Bounded, Sub-Second Ingestion & Real-Time Voice/WhatsApp Escalation Engine*

---

##  Executive Summary & Core Value Proposition

Failed transactions and cart abandonments cost merchants billions in lost Gross Merchandise Value (GMV). Traditional recovery mechanisms rely on blind, static cron jobs that create customer fatigue and violate regulatory payment retry thresholds.

**AutoRecover OS** is an intelligent, edge-first payment recovery operating system designed for modern fintech infrastructure:
1. **Local Fine-Tuned SLM (Primary Engine):** 4-bit quantized **Qwen-2.5-3B-Instruct** running directly on an NVIDIA RTX 4060 for sub-100ms structured root-cause diagnosis with zero recurring API costs.
2. **Autonomous Cloud Failover:** Dual-layer redundancy falling back to **Google Gemini** if local GPU resources are constrained.
3. **Temporal State Machine with Time Compression:** Asynchronous event ledger enforcing progressive backoff intervals, salary-window alignment, and hard RBI compliance stops (3 retries / opt-out termination).
4. **Multimodal Customer Engagement:** On-the-fly **Microsoft Neural Hinglish Audio Voice Notes** combined with native **Meta WhatsApp Cloud API** interactive payment & opt-out CTA buttons.
5. **Operational Audit & Escalation Engine:** Immutable audit logging with instant segregated CSV reports for operations and finance teams.

---

##  System Architecture

```
                                  [ Incoming Payment Stream ]
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │  recovery_ledger.db (SQLite)    │
                             │  • Asynchronous Event Bus       │
                             │  • Temporal State Machine       │
                             └─────────────────────────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │   engine/classifier.py          │
                             │   Bounded Workflow Orchestrator │
                             └─────────────────────────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       ▼                                             ▼
         ┌───────────────────────────┐                 ┌───────────────────────────┐
         │  [Primary] Local 3B SLM   │                 │  [Failover] Google Gemini │
         │  • Qwen-2.5-3B-Instruct   │  (If GPU OOM)   │  • Structured Schema      │
         │  • 4-Bit QLoRA on RTX 4060│ ───────────────>│  • Sub-Second Cloud JSON │
         │  • 0 API Inference Cost   │                 │  • Zero-Downtime Guarantee│
         └───────────────────────────┘                 └───────────────────────────┘
                       │                                             │
                       └──────────────────────┬──────────────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │   engine/dispatcher.py          │
                             │   Multimodal Outreach Layer     │
                             ├─────────────────────────────────┤
                             │ • Edge-TTS Hinglish Voice Note  │
                             │ • Meta WhatsApp Interactive API │
                             │ • Whitelisted Security Guard    │
                             └─────────────────────────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │   Streamlit Real-Time Dashboard │
                             │   • Sub-second Live Polling     │
                             │   • In-Browser Voice Player     │
                             │   • Segregated Audit CSV Export │
                             └─────────────────────────────────┘



  
Complete Local Environment Setup & Execution Guide

### 1. Prerequisites & Environment Initialization

Install **Python 3.11** using `winget` (Windows Package Manager) if not already present:

```powershell
winget install Python.Python.3.11

Create and activate an isolated virtual environment using Python 3.11:

PowerShell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1

2. Dependency Installation
A. Install PyTorch with CUDA 12.4 (NVIDIA GPU Acceleration)
PowerShell
pip install torch torchvision --index-url [https://download.pytorch.org/whl/cu124](https://download.pytorch.org/whl/cu124)
B. Install Core LLM, Fine-Tuning & Quantization Stack
PowerShell
pip install transformers datasets peft bitsandbytes accelerate
pip install trl==0.12.2
C. Install Dashboard, Schemas, Telemetry & Integration Libraries
PowerShell
pip install streamlit plotly pydantic>=2.0.0 python-dotenv>=1.0.0 google-genai>=0.1.1,<3.0.0 tabulate>=0.9.0 edge-tts requests
(Optional alternative if using a unified requirements.txt:)

PowerShell
pip install -r requirements.txt

4. Environment Variables Configuration (.env)
Create a .env file in the root project folder (pay-ai/.env) and add your credentials:

Ini, TOML
# Google Cloud Gemini API Configuration (Failover)
GEMINI_API_KEY=your_gemini_api_key_here

# Meta WhatsApp Cloud Graph API Configuration
META_WA_TOKEN=your_meta_whatsapp_access_token_here
META_PHONE_ID=your_meta_phone_number_id_here

# Security Guard: Whitelisted Target Test Phone (Country code without '+')
TARGET_TEST_PHONE=91xxxxxxxxx
5. Running the System (Dual-Terminal Execution)
Terminal 1: Real-Time Streamlit Dashboard & Temporal Worker
Open your first terminal to start the live monitoring interface and background execution worker:

PowerShell
.\venv\Scripts\Activate.ps1
streamlit run app.py
Dashboard URL: http://localhost:8501

Terminal 2: Event Stream Generator & Benchmark Controller
Open a second terminal to emit live payments or seed the 50-transaction benchmark:

PowerShell
.\venv\Scripts\Activate.ps1
python generator_daemon.py
Benchmark Controller Options:

1 — Single Live Event: Emits a single transaction, runs local 3B model inference, synthesizes Edge-TTS Hinglish voice audio, and delivers interactive WhatsApp CTA buttons to your verified device.

2 — Benchmark 50 Dataset: Ingests 50 structured transactions (30 Direct Successes, 15 Multi-Step Staged Recoveries with dynamic backoff, and 5 Compliance-Terminated Lost Revenues).

3 — Clear Ledger: Resets and truncates the SQLite database ledger cleanly.

6. Audit & Escalation Reporting
Chronological Audit CSV: Exports timestamped transaction trails with retry counters and diagnostic reasons.

Segregated Escalation Batch CSV: Prioritizes Revenue Lost / Terminated transactions at the top for financial review, followed by Multi-Attempt Recovered cases with full retry logs.


---

### Summary of `requirements.txt`

You can also package these dependencies cleanly into a `requirements.txt` file in your repository:


torch>=2.4.0
torchvision
transformers>=4.44.0
peft>=0.12.0
bitsandbytes>=0.43.0
accelerate>=0.33.0
trl==0.12.2
datasets
streamlit>=1.38.0
plotly>=5.22.0
pandas>=2.2.0
pydantic>=2.0.0
python-dotenv>=1.0.0
google-genai>=0.1.1,<3.0.0
tabulate>=0.9.0
edge-tts>=6.1.12
requests>=2.31.0
