import random
from schemas import PaymentEvent, WorkflowDecision, ExecutionTrace, ActionType

def execute_bounded_workflow(event: PaymentEvent, decision: WorkflowDecision) -> ExecutionTrace:
    logs = []
    recovered = False
    amount_recovered = 0.0
    steps_run = 0

    logs.append(f"[{event.transaction_id}] [{event.category.value}] Diagnosed: {decision.root_cause_diagnosis}")

    for step in decision.workflow_steps:
        steps_run += 1
        if step.action == ActionType.TERMINATE:
            logs.append(f"🛑 Step {step.step_number}: {step.reason_context}")
            break

        logs.append(f"⚡ Step {step.step_number} (T+{step.scheduled_delay_minutes}m): Executed {step.action.value} on {step.channel}")

        # Recovery probability per channel
        prob = 0.88 if step.action in [ActionType.WHATSAPP_FAST_PAY, ActionType.HINGLISH_VOICE_NUDGE] else 0.74
        if random.random() < prob:
            recovered = True
            discount_factor = 1.0 - (decision.recovery_incentive_pct / 100.0)
            amount_recovered = round(event.amount_inr * discount_factor, 2)
            logs.append(f"✅ Recovered ₹{amount_recovered:,.2f} at Step {step.step_number} (Incentive: {decision.recovery_incentive_pct}%)")
            break
        else:
            logs.append(f"⚠️ Step {step.step_number} response pending/unresolved. Escalating...")

    final_status = "RECOVERED" if recovered else "UNRECOVERED"
    if not recovered and steps_run > 0:
        logs.append("🛑 Workflow bounds completed. Awaiting manual finance review.")

    return ExecutionTrace(
        transaction_id=event.transaction_id,
        customer_name=event.customer_name,
        category=event.category,
        amount_at_risk=event.amount_inr,
        failure_reason=event.failure_reason,
        workflow_summary=f"{decision.primary_action.value} ({steps_run} Steps)",
        final_status=final_status,
        recovered_amount=amount_recovered,
        steps_taken=steps_run,
        hinglish_log=decision.hinglish_script,
        ptp_status=f"PTP Date: {decision.ptp_date_assigned}" if decision.ptp_date_assigned else None,
        audit_trail=logs
    )