# ⚡ AutoRecover OS: Autonomous Payment Recovery Engine

> **Autonomous agent that detects revenue at risk, diagnoses root cause via hybrid SLM/LLM inference, and executes bounded, compliant recovery workflows with neural Hinglish voice notes and interactive WhatsApp automation.**

---

## 📌 Executive Summary & Problem Context

Revenue loss in modern fintech and digital commerce rarely happens in a single, clean step. It begins with a degraded payment rail, an abandoned checkout session, a failed mandate auto-debit, or an overdue B2B enterprise invoice. Traditional dunning solutions and payment gateways either drop failed transactions immediately or spam users with generic, high-friction SMS alerts that result in customer churn, high bank charges, and regulatory violations.

**AutoRecover OS** closes this loop. It provides an end-to-end autonomous recovery state machine that ingests gateway failures, classifies the exact technical or behavioral root cause, synthesizes context-aware Hinglish voice notes, dispatches 2-way interactive WhatsApp actions, enforces strict compliance stopping rules, and measures total money won back across high-volume transaction batches.

---

## 🚀 Key Architectural Innovations & Differentiators

- **SLM-First Dual-Tier AI Architecture:** Uses a fine-tuned local **Qwen-2.5-3B** SLM for sub-second, zero-cost root cause diagnosis and dynamic workflow generation, with **Google Gemini API** acting as a high-availability fallback circuit breaker.
- **Neural Multimodal Recovery:** Dispatches human-like, conversational Hinglish audio messages synthesized via **Microsoft Edge-TTS** (`hi-IN-SwaraNeural`) alongside 1-click **Meta WhatsApp Interactive CTAs** (`Pay Now` / `Opt-Out`).
- **Deterministic Bounded Workflows:** Prevents infinite recovery loops by enforcing strict state-machine bounds (maximum 3 retry attempts, dynamic backoff curves, and instant customer opt-out termination).
- **Promise-to-Pay (PTP) Calendar Locking:** Automatically detects and registers explicit customer payment commitments, freezing dunning cadence until the agreed commitment date.
- **Dual-Mode Demo Scaling:** Features an authentic single-transaction live webhook callback integration paired with an enterprise 50-transaction benchmark operating on a realistic time-compression scale.
- **Financial & Engineering Reconciliation:** Generates two segregated, production-ready CSV audit reports separating chronological logs from prioritized engineering/financial escalations.

---

## ⏱️ Real-World Time-Compression Scale

To demonstrate 30-day temporal lifecycle orchestration within short demo windows, the state machine operates on a compressed time scale where seconds map directly to production operational timelines:

| Demo Duration | Real-World Scale | Failure Scenario & Strategy | Business Impact |
| :--- | :--- | :--- | :--- |
| **3s – 4s** | 15 – 30 Minutes | `CHECKOUT_DROPOFF` / `PACKET_LOSS` | High-intent instant checkout recovery before cart abandonment. |
| **6s – 8s** | 2 – 4 Hours | `PAYMENT_DEGRADATION` / `BANK_DOWNTIME` | Transient downtime backoff; waits for issuing bank TPS stabilization. |
| **10s – 12s** | 24 Hours (Next Day) | `MANDATE_RETRY` / `INSUFFICIENT_FUNDS` | Re-presents auto-debit cycles during morning salary clearing windows. |
| **15s – 20s** | 3 – 7 Days | `FAILED_SUBSCRIPTION` / `EXPIRED_CARD` | SaaS dunning grace period allowing customer billing update. |
| **288s** | 30 – 45 Days | `B2B_RECEIVABLES` / `MANDATE_REJECTED` | Enterprise Net-45 AR dunning, PTP tracking, and CFO escalation. |
| **Stopping Rule** | 45+ Days / 3 Retries | **Compliance Ceiling / Opt-Out** | Instant halt to prevent harassment and ensure RBI/NPCI compliance. |

---

## 🛠️ Complete Tech Stack

- **Inference Engine:** Qwen-2.5-3B-Instruct (Ollama / Local Runtime) • Google Gemini API (Failover)
- **Voice Synthesis:** Microsoft Edge-TTS (`hi-IN-SwaraNeural`)
- **Communication Layer:** Meta WhatsApp Cloud API (Graph API v20.0) • FastAPI Webhook Engine
- **Temporal State Ledger:** SQLite (WAL Mode) • Python Async Temporal Worker
- **Frontend & Monitoring:** Streamlit (`@st.fragment` 1s polling) • Plotly Express
- **Tunneling & Security:** Cloudflare Tunnels (`cloudflared`)

---

## 📂 Repository Structure

```text
pay-ai/
├── app.py                     # Streamlit real-time monitoring dashboard & temporal worker
├── webhook_server.py          # FastAPI listener for Meta WhatsApp events & audio hosting
├── generator_daemon.py        # Interactive CLI traffic controller (Option 1 & Option 2)
├── test_meta.py               # Standalone Meta WhatsApp Cloud API diagnostic ping
├── db.py                      # SQLite ledger, schema initialization, and transactional state queries
├── schemas.py                 # Pydantic data contracts, enums, and structured output models
├── engine/
│   ├── classifier.py          # Root-cause diagnosis & workflow planner (Qwen-2.5 / Gemini)
│   └── dispatcher.py          # Voice synthesis engine & Meta WhatsApp message dispatcher
├── static/
│   └── audio/                 # Generated Hinglish voice notes (.mp3)
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables and API credentials
```

---

## ⚙️ Setup & Installation

### 1. Clone the Repository & Set Up Virtual Environment

```bash
git clone https://github.com/your-username/pay-ai.git
cd pay-ai
python -m venv venv
```

Activate the virtual environment:

- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
- **Linux/macOS:** `source venv/bin/activate`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```ini
# Meta WhatsApp Cloud API Credentials
META_WA_TOKEN=EAA...your_meta_access_token...
META_PHONE_ID=your_meta_phone_number_id
TARGET_TEST_PHONE=916381121659

# Public Reverse Proxy Endpoint (from Cloudflare Tunnel)
PUBLIC_SERVER_URL=https://your-domain.trycloudflare.com

# AI Model Configuration
GEMINI_API_KEY=your_gemini_api_key
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Dependency Installation (Detailed)

**A. Install PyTorch with CUDA 12.4 (NVIDIA GPU Acceleration)**

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

**B. Install Core LLM, Fine-Tuning & Quantization Stack**

```bash
pip install transformers datasets peft bitsandbytes accelerate
pip install trl==0.12.2
```

**C. Install Dashboard, Schemas, Telemetry & Integration Libraries**

```bash
pip install streamlit plotly pydantic>=2.0.0 python-dotenv>=1.0.0 google-genai>=0.1.1,<3.0.0 tabulate>=0.9.0 edge-tts requests
```

*(Or, if using the unified `requirements.txt`, simply run `pip install -r requirements.txt`.)*

**`requirements.txt` reference:**

```text
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
```

---

## 🎮 Execution & Demo Guide

Run the following services across dedicated terminal windows:

**Terminal 1: Cloudflare Public HTTPS Tunnel**

```bash
cloudflared tunnel --url http://localhost:8000
```

Copy the output `https://xxxx.trycloudflare.com` URL into `PUBLIC_SERVER_URL` in `.env`.

**Terminal 2: Webhook & Audio Server**

```bash
python webhook_server.py
```

**Terminal 3: Streamlit Operational Dashboard**

```bash
streamlit run app.py
```

Open your browser at: `http://localhost:8501`

**Terminal 4: Event Generator & Benchmark Controller**

```bash
python generator_daemon.py
```

- **Option 1 (Single Live Interactive Event):** Emits a real-time checkout drop-off transaction, generates a custom neural Hinglish voice note, and dispatches an interactive WhatsApp message to your phone.
- **Option 2 (Benchmark 50 Dataset):** Seeds 50 transactions across 5 failure categories demonstrating dynamic recovery throughput, retry backoff intervals, and compliance termination.

---

## 📊 Exportable Audit Artifacts

AutoRecover OS guarantees end-to-end reconciliation and triage via two structured CSV exports:

- **Chronological Audit CSV:** Complete transaction lifecycle history, timestamps, failure reasons, retry attempt counts, and step-by-step execution logs.
- **Segregated Escalation Batch CSV:** Actionable financial and engineering report prioritized into:
  - **P1 - REVENUE LOST:** Transactions terminated due to customer opt-out or max retry limits exceeding compliance thresholds.
  - **P2 - DEGRADED BUT RESOLVED:** Multi-attempt retry recoveries resolved across alternative payment rails.

---

## 🏗️ End-to-End System Architecture

```
                                  +-------------------------------------------------------------------+
                                  |                     TRANSACTION INGESTION LAYER                   |
                                  |    (Checkout Drop-offs, Mandate Failures, Bank Drops, B2B AR)      |
                                  +-------------------------------------------------------------------+
                                                                    │
                                                                    ▼
                                  +-------------------------------------------------------------------+
                                  |                 DUAL-TIER AI DIAGNOSTIC ENGINE                    |
                                  |   ┌───────────────────────────────────────────────────────────┐   |
                                  |   │ Primary: Qwen-2.5-3B Local SLM (Zero Cost, <500ms Latency) │   |
                                  |   │ Fallback: Google Gemini API Circuit Breaker                │   |
                                  |   └───────────────────────────────────────────────────────────┘   |
                                  +-------------------------------------------------------------------+
                                                                    │
                                            ┌───────────────────────┴───────────────────────┐
                                            ▼                                                ▼
                         +-------------------------------------+         +-------------------------------------+
                         |      BOUNDED WORKFLOW PLANNER        |         |        NEURAL VOICE SYNTHESIS       |
                         |  - Adaptive Retry Backoff (3s-288s)  |         |  - Microsoft Edge-TTS Engine        |
                         |  - PTP Commitment Lock Engine        |         |  - Contextual Hinglish Scripting    |
                         |  - Max 3 Retries & Opt-Out Bounds    |         |  - Output: /static/audio/{id}.mp3   |
                         +-------------------------------------+         +-------------------------------------+
                                            │                                                │
                                            └───────────────────────┬───────────────────────┘
                                                                    │
                                                                    ▼
                                  +-------------------------------------------------------------------+
                                  |                 OMNICHANNEL DISPATCH & GATEWAY                    |
                                  |               Meta WhatsApp Cloud API (v20.0)                     |
                                  |   ┌───────────────────────────────────────────────────────────┐   |
                                  |   │ [🔊 Neural Audio] + [⚡ Dynamic Context] + [CTA Buttons]   │   |
                                  |   └───────────────────────────────────────────────────────────┘   |
                                  +-------------------------------------------------------------------+
                                                                    │
                                                                    ▼
                                  +-------------------------------------------------------------------+
                                  |                    CUSTOMER INTERACTION LAYER                     |
                                  |                  (Mobile WhatsApp Client)                         |
                                  |   ┌────────────────────────────────┬───────────────────────────┐  |
                                  |   │ [✅ Pay Now (1-Click FastPay)] │ [🛑 Stop / Opt-Out]        │  |
                                  |   └────────────────────────────────┴───────────────────────────┘  |
                                  +-------------------------------------------------------------------+
                                                                    │
                                                                    ▼
                                  +-------------------------------------------------------------------+
                                  |                   INBOUND WEBHOOK ROUTING LAYER                   |
                                  |             FastAPI Server (Port 8000 via Cloudflare Tunnel)      |
                                  |   - Captures Interactive Button Replies & Plaintext Callbacks     |
                                  +-------------------------------------------------------------------+
                                                                    │
                                                                    ▼
                                  +-------------------------------------------------------------------+
                                  |                 TEMPORAL STATE MACHINE & LEDGER                   |
                                  |                      SQLite (WAL Mode Engine)                     |
                                  |   ┌────────────────────────────────┬───────────────────────────┐  |
                                  |   │ Status: RECOVERED (Won Back)   │ Status: TERMINATED (Stop) │  |
                                  |   └────────────────────────────────┴───────────────────────────┘  |
                                  +-------------------------------------------------------------------+
                                                                    │
                                                                    ▼
                                  +-------------------------------------------------------------------+
                                  |                 ANALYTICS & RECONCILIATION LAYER                  |
                                  |   ┌───────────────────────────────────────────────────────────┐   |
                                  |   │ Streamlit Live Dashboard (@st.fragment 1-sec Polling)      │   |
                                  |   │ Chronological Audit CSV • Segregated Escalation Batch CSV  │   |
                                  |   └───────────────────────────────────────────────────────────┘   |
                                  +-------------------------------------------------------------------+
```