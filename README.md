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

```text
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
