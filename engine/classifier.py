from typing import Optional
from schemas import PaymentEvent, WorkflowDecision, WorkflowStep, ActionType, FailureReason, RecoveryCategory
from engine.agent import generate_hinglish_voice_script

def evaluate_bounded_workflow(event: PaymentEvent) -> WorkflowDecision:
    """Enforces strict stopping rules and deterministic recovery workflows across all 7 tracks."""
    
    # HARD STOPPING RULES (The Bar)
    if event.customer_opt_out or event.retry_count >= 3:
        return WorkflowDecision(
            category=event.category,
            primary_action=ActionType.TERMINATE,
            workflow_steps=[
                WorkflowStep(
                    step_number=1,
                    scheduled_delay_minutes=0,
                    action=ActionType.TERMINATE,
                    channel="NONE",
                    reason_context="Compliance Stop: Reached 3 retry attempts or explicit opt-out."
                )
            ],
            root_cause_diagnosis="Terminated to prevent customer harassment and comply with RBI/NPCI limits."
        )

    # 1. PAYMENT DEGRADATION (Bank Downtime / Packet Loss)
    if event.category == RecoveryCategory.PAYMENT_DEGRADATION:
        delay = 10 if event.failure_reason == FailureReason.PACKET_LOSS else 90
        return WorkflowDecision(
            category=event.category,
            primary_action=ActionType.SILENT_MANDATE_RETRY,
            workflow_steps=[
                WorkflowStep(
                    step_number=1,
                    scheduled_delay_minutes=delay,
                    action=ActionType.SILENT_MANDATE_RETRY,
                    channel="API_GATEWAY",
                    reason_context=f"Degradation detected. Silent retry scheduled in {delay}m after bank node recovery."
                )
            ],
            root_cause_diagnosis="Infrastructure node degradation. Zero customer friction recovery."
        )

    # 2. CHECKOUT DROP-OFF RECOVERY
    if event.category == RecoveryCategory.CHECKOUT_DROPOFF:
        script = generate_hinglish_voice_script(event.customer_name, event.amount_inr, "https://rzp.io/l/quick_chk")
        return WorkflowDecision(
            category=event.category,
            primary_action=ActionType.WHATSAPP_FAST_PAY,
            workflow_steps=[
                WorkflowStep(
                    step_number=1,
                    scheduled_delay_minutes=5,
                    action=ActionType.WHATSAPP_FAST_PAY,
                    channel="WHATSAPP_UPI_QR",
                    message_content=script,
                    reason_context="OTP friction detected. Dispatched 1-click UPI QR checkout link."
                )
            ],
            root_cause_diagnosis="Checkout funnel drop-off resolved via instant WhatsApp fast-pay.",
            hinglish_script=script,
            recovery_incentive_pct=3.0 if event.amount_inr > 5000 else 0.0
        )

    # 3. MANDATE RETRY SEQUENCER (NPCI AutoPay Window 8AM - 8PM)
    if event.category == RecoveryCategory.MANDATE_RETRY:
        return WorkflowDecision(
            category=event.category,
            primary_action=ActionType.SILENT_MANDATE_RETRY,
            workflow_steps=[
                WorkflowStep(
                    step_number=1,
                    scheduled_delay_minutes=360,
                    action=ActionType.SILENT_MANDATE_RETRY,
                    channel="NPCI_AUTOPAY_API",
                    reason_context="Mandate queued for NPCI active clearance window (08:00 - 20:00 IST)."
                ),
                WorkflowStep(
                    step_number=2,
                    scheduled_delay_minutes=1440,
                    action=ActionType.WHATSAPP_FAST_PAY,
                    channel="WHATSAPP",
                    reason_context="Secondary escalation if balance remains insufficient."
                )
            ],
            root_cause_diagnosis="AutoPay mandate retry synced with banking salary window."
        )

    # 4. B2B RECEIVABLES CHASER & PROMISE-TO-PAY (PTP) TRACKER
    if event.category == RecoveryCategory.B2B_RECEIVABLES:
        ptp_date = event.promised_pay_date or "2026-09-08"
        return WorkflowDecision(
            category=event.category,
            primary_action=ActionType.PTP_LOGGED if event.days_overdue < 30 else ActionType.B2B_ESCALATION_EMAIL,
            workflow_steps=[
                WorkflowStep(
                    step_number=1,
                    scheduled_delay_minutes=0,
                    action=ActionType.PTP_LOGGED,
                    channel="FINANCE_PORTAL",
                    reason_context=f"Logged Promise-to-Pay (PTP) agreement for {ptp_date}."
                ),
                WorkflowStep(
                    step_number=2,
                    scheduled_delay_minutes=2880,
                    action=ActionType.B2B_ESCALATION_EMAIL,
                    channel="EMAIL_CFO",
                    reason_context="Automated ledger reconciliation and escalation email to accounts payable."
                )
            ],
            root_cause_diagnosis=f"B2B invoice overdue by {event.days_overdue} days. Active PTP tracking engaged.",
            ptp_date_assigned=ptp_date
        )

    # 5. FAILED SUBSCRIPTION RECOVERY (Card expired / Dunning)
    script = f"Aapka subscription renew nahi ho paya. Apna payment method yahan update karein: https://rzp.io/s/sub_upd"
    return WorkflowDecision(
        category=event.category,
        primary_action=ActionType.HINGLISH_VOICE_NUDGE,
        workflow_steps=[
            WorkflowStep(
                step_number=1,
                scheduled_delay_minutes=60,
                action=ActionType.HINGLISH_VOICE_NUDGE,
                channel="WHATSAPP_VOICE",
                message_content=script,
                reason_context="Subscription payment method renewal dispatched via localized reminder."
            )
        ],
        root_cause_diagnosis="Recurring card token expired. Triggered dunning update cycle.",
        hinglish_script=script
    )