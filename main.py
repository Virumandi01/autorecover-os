from tabulate import tabulate
from generator import generate_mock_events
from engine.classifier import rule_based_triage
from engine.agent import diagnose_and_decide
from engine.guardrails import apply_guardrails
from engine.executor import execute_recovery

def run_recovery_pipeline(batch_size: int = 50):
    print("=" * 70)
    print(f"🚀 INGESTING {batch_size} FAILED PAYMENT EVENTS INTO AUTORECOVER OS...")
    print("=" * 70)

    events = generate_mock_events(batch_size)

    total_at_risk = 0.0
    total_recovered = 0.0
    rule_triage_count = 0
    llm_triage_count = 0
    audit_table = []

    for event in events:
        total_at_risk += event.amount_inr
        
        # Step 1: Zero-Token Rule Classifier
        decision = rule_based_triage(event)
        if decision:
            rule_triage_count += 1
            source = "RULES (0-Tokens)"
        else:
            # Step 2: LLM Diagnostics Agent
            decision = diagnose_and_decide(event)
            llm_triage_count += 1
            source = "LLM AGENT"

        # Step 3: Guardrails Intercept
        guarded_decision = apply_guardrails(event, decision)

        # Step 4: Execution & Audit Logging
        result = execute_recovery(event, guarded_decision)
        if result.recovered:
            total_recovered += result.amount_recovered

        audit_table.append([
            event.transaction_id,
            f"₹{event.amount_inr:.2f}",
            event.failure_reason.value,
            source,
            guarded_decision.action.value,
            " YES" if result.recovered else "NO",
            f"₹{result.amount_recovered:.2f}"
        ])

    # Print Detailed Audit Trail (First 15 sample records for scannability)
    headers = ["Txn ID", "Amount", "Reason", "Triaged By", "Action", "Recovered", "Recovered Amount"]
    print("\n--- AUDIT TRAIL LOG (SAMPLE 15 OF BATCH) ---")
    print(tabulate(audit_table[:15], headers=headers, tablefmt="github"))

    # Print Final Financial & Performance Metrics
    recovery_rate = (total_recovered / total_at_risk) * 100 if total_at_risk > 0 else 0
    print("\n" + "=" * 70)
    print("📊 REVENUE RECOVERY PERFORMANCE REPORT")
    print("=" * 70)
    print(f"Total Revenue At Risk:       ₹{total_at_risk:,.2f}")
    print(f"Total Revenue Recovered:     ₹{total_recovered:,.2f}")
    print(f"Net Recovery Efficiency:     {recovery_rate:.2f}%")
    print(f"Rule Triage (0-Token Path):  {rule_triage_count} transactions ({(rule_triage_count/batch_size)*100:.1f}%)")
    print(f"Agent Triage (LLM Path):     {llm_triage_count} transactions ({(llm_triage_count/batch_size)*100:.1f}%)")
    print("=" * 70)

if __name__ == "__main__":
    run_recovery_pipeline(batch_size=50)