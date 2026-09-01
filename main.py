from tabulate import tabulate
from generator import generate_mock_events
from engine.classifier import evaluate_bounded_workflow
from engine.agent import diagnose_and_decide
from engine.guardrails import apply_guardrails
from engine.executor import execute_bounded_workflow
from schemas import WorkflowDecision, WorkflowStep

def run_recovery_pipeline(batch_size: int = 50):
    print("=" * 70)
    print(f"🚀 INGESTING {batch_size} FAILED PAYMENT EVENTS INTO AUTORECOVER OS...")
    print("=" * 70)

    events = generate_mock_events(batch_size)

    total_at_risk = 0.0
    total_recovered = 0.0
    audit_table = []

    for event in events:
        total_at_risk += event.amount_inr
        
        # Step 1: Evaluate Bounded Workflow
        decision = evaluate_bounded_workflow(event)
        
        if not decision:
            # Step 2: Fallback to LLM Agent if not covered by direct rule
            llm_dec = diagnose_and_decide(event)
            guarded = apply_guardrails(event, llm_dec)
            decision = WorkflowDecision(
                primary_action=guarded.action,
                initial_delay_minutes=guarded.scheduled_hour_delay * 60,
                workflow_steps=[
                    WorkflowStep(
                        step_number=1,
                        scheduled_delay_minutes=guarded.scheduled_hour_delay * 60,
                        channel=guarded.target_channel,
                        action=guarded.action,
                        reason_context=guarded.rationale
                    )
                ],
                root_cause_diagnosis=guarded.rationale,
                recovery_incentive_pct=guarded.incentive_discount_pct
            )

        # Step 3: Execute Workflow
        trace = execute_bounded_workflow(event, decision)
        total_recovered += trace.recovered_amount

        audit_table.append([
            trace.transaction_id,
            f"₹{trace.amount_at_risk:.2f}",
            trace.failure_reason.value,
            trace.workflow_executed,
            "✅ YES" if trace.final_status == "RECOVERED" else "❌ NO",
            f"₹{trace.recovered_amount:.2f}"
        ])

    headers = ["Txn ID", "At Risk", "Failure Reason", "Workflow Executed", "Recovered", "Amount Won Back"]
    print("\n--- AUDIT TRAIL LOG (SAMPLE 15 RECORDS) ---")
    print(tabulate(audit_table[:15], headers=headers, tablefmt="github"))

    recovery_rate = (total_recovered / total_at_risk) * 100 if total_at_risk > 0 else 0
    print("\n" + "=" * 70)
    print("📊 REVENUE RECOVERY PERFORMANCE REPORT")
    print("=" * 70)
    print(f"Total Revenue At Risk:       ₹{total_at_risk:,.2f}")
    print(f"Total Revenue Recovered:     ₹{total_recovered:,.2f}")
    print(f"Net Recovery Efficiency:     {recovery_rate:.2f}%")
    print("=" * 70)

if __name__ == "__main__":
    run_recovery_pipeline(batch_size=50)