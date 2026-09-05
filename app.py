import os
import json
import random
import io
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.express as px
from db import init_db, get_db, get_due_recovery_jobs, schedule_next_retry, finalize_transaction, clear_all_transactions
from engine.classifier import evaluate_bounded_workflow
from engine.dispatcher import synthesize_hinglish_voice, send_real_whatsapp_interactive
from schemas import PaymentEvent, RecoveryCategory, FailureReason

st.set_page_config(page_title="AutoRecover OS | Payment Recovery Engine", page_icon="⚡", layout="wide")
init_db()

with st.sidebar.expander("⏱️ Demo Time-Compression Scale", expanded=True):
    st.markdown("""
    | Demo Time | Real-World Scale | Category & Purpose |
    | :--- | :--- | :--- |
    | **3s – 4s** | **15 – 30 Mins** | `CHECKOUT_DROPOFF` (Instant Nudge) |
    | **6s – 8s** | **2 – 4 Hours** | `BANK_DOWNTIME` (Core Bank Reset) |
    | **10s – 12s** | **24 Hours** | `MANDATE_RETRY` (Salary Re-presentment) |
    | **15s – 20s** | **3 – 7 Days** | `FAILED_SUBSCRIPTION` (Card Grace Period) |
    | **288s** | **30 – 45 Days** | `B2B_RECEIVABLES` (Enterprise PTP & AR Dunning) |
    | **Final Stop** | **45+ Days** | Max 3 Retries / Compliance Termination |
    """)

# --- TEMPORAL RECOVERY WORKER ---
def run_temporal_recovery_worker():
    due_jobs = get_due_recovery_jobs()
    for row in due_jobs:
        txn_id = row["id"]
        step = row["current_step"] + 1

        # 1. Check if this is the live single test transaction (Wait exclusively for WhatsApp webhook button click)
        is_live_interactive = (row.get("customer_phone") == os.getenv("TARGET_TEST_PHONE") and row["category"] == "CHECKOUT_DROPOFF")

        if is_live_interactive:
            # DO NOT re-dispatch WhatsApp message or auto-randomize. Keep waiting for user button action.
            continue
        
        ev = PaymentEvent(
            transaction_id=txn_id,
            customer_id=f"CUST_{txn_id[-4:]}",
            customer_name=row["customer_name"],
            category=RecoveryCategory(row["category"]),
            amount_inr=row["amount_inr"],
            channel=row["channel"],
            failure_reason=FailureReason(row["failure_reason"]) if row["failure_reason"] else FailureReason.PACKET_LOSS,
            retry_count=step - 1,
            days_overdue=row["days_overdue"],
            is_salary_account=bool(row["is_salary_account"]),
            customer_opt_out=bool(row["customer_opt_out"]),
            promised_pay_date=row["promised_pay_date"]
        )

        decision = evaluate_bounded_workflow(ev)
        
        # Stopping rule check
        if row["customer_opt_out"] or step > row["max_steps"]:
            finalize_transaction(
                txn_id, "TERMINATED", 0.0,
                f"🛑 [{datetime.now().strftime('%H:%M:%S')}] Step {step} Compliance Stop: Max retries exceeded ({row['max_steps']}) or customer opt-out."
            )
            continue

        target_step = decision.workflow_steps[min(step - 1, len(decision.workflow_steps) - 1)]
        scaled_delay_sec = max(3, int(target_step.scheduled_delay_minutes / 10)) if target_step.scheduled_delay_minutes > 0 else 4
        next_eta = (datetime.now() + timedelta(seconds=scaled_delay_sec)).isoformat()

        audio_path = row.get("voice_audio_path")
        hinglish_msg = decision.hinglish_script
        if hinglish_msg and not audio_path:
            audio_path = synthesize_hinglish_voice(hinglish_msg, txn_id)

        # 60% probability of success per retry for benchmark dataset
        is_recovered = random.random() < 0.60
        if is_recovered:
            finalize_transaction(
                txn_id, "RECOVERED", row["amount_inr"],
                f"✅ [{datetime.now().strftime('%H:%M:%S')}] Step {step} Success: {target_step.action.value} recovered ₹{row['amount_inr']:,.2f} via {target_step.channel}"
            )
        else:
            schedule_next_retry(
                txn_id=txn_id,
                next_attempt_at=next_eta,
                step_num=step,
                log_entry=f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Step {step} Failed ({target_step.action.value}). Scheduled retry step in {scaled_delay_sec}s.",
                summary=f"{target_step.action.value} (Step {step}/{row['max_steps']})",
                hinglish=hinglish_msg,
                audio_path=audio_path
            )

def build_chronological_csv(df: pd.DataFrame) -> str:
    df_sorted = df.sort_values(by="created_at", ascending=False).copy()
    export_df = pd.DataFrame({
        "Timestamp": df_sorted["created_at"],
        "Transaction ID": df_sorted["id"],
        "Customer Name": df_sorted["customer_name"],
        "Category": df_sorted["category"],
        "Amount (INR)": df_sorted["amount_inr"],
        "Payment Channel": df_sorted["channel"],
        "Lifecycle Status": df_sorted["status"],
        "Initial Failure Reason": df_sorted["failure_reason"].fillna("None (Instant Success)"),
        "Recovered Amount": df_sorted["recovered_amount"],
        "Active Workflow Step": df_sorted["workflow_summary"].fillna("None"),
        "Retry Attempts Made": df_sorted["current_step"],
        "Audit Trail History": df_sorted["audit_trail"]
    })
    return export_df.to_csv(index=False)

def build_escalation_csv(df: pd.DataFrame) -> str:
    df_lost = df[df["status"] == "TERMINATED"].copy()
    df_lost["Escalation Priority"] = "P1 - REVENUE LOST (Terminated / Compliance Exceeded)"

    df_errored = df[df["status"].isin(["PENDING_RETRY", "RECOVERED"]) & df["failure_reason"].notna()].copy()
    df_errored["Escalation Priority"] = "P2 - DEGRADED BUT RESOLVED (Multi-Attempt Retry)"

    combined_escalation = pd.concat([df_lost, df_errored], ignore_index=True)

    if combined_escalation.empty:
        return pd.DataFrame({"Message": ["No escalated or errored transactions currently on record."]}).to_csv(index=False)

    export_df = pd.DataFrame({
        "Escalation Priority": combined_escalation["Escalation Priority"],
        "Timestamp": combined_escalation["created_at"],
        "Transaction ID": combined_escalation["id"],
        "Customer Name": combined_escalation["customer_name"],
        "Category": combined_escalation["category"],
        "Amount At Risk (INR)": combined_escalation["amount_inr"],
        "Current Status": combined_escalation["status"],
        "Initial Failure Reason": combined_escalation["failure_reason"],
        "Total Retries Done": combined_escalation["current_step"],
        "Recovered Amount": combined_escalation["recovered_amount"],
        "Workflow Action Executed": combined_escalation["workflow_summary"],
        "Hinglish Communication Sent": combined_escalation["hinglish_script"].fillna("None"),
        "Step-by-Step Error & Audit Trail": combined_escalation["audit_trail"]
    })
    return export_df.to_csv(index=False)

# Top Bar Header
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.title("⚡ AutoRecover OS: Autonomous Gateway Engine")
    st.caption("Temporal State Machine • Qwen-2.5-3B Local SLM • Edge-TTS Neural Voice • WhatsApp Interactive Bridge")
with col_btn:
    st.write("")
    if st.button("🗑️ Clear Database Ledger", width="stretch"):
        clear_all_transactions()
        st.success("Ledger reset.")
        st.rerun()

# --- REAL-TIME STREAMING DASHBOARD ---
@st.fragment(run_every="1s")
def render_live_temporal_dashboard():
    run_temporal_recovery_worker()

    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY created_at DESC", conn)
    conn.close()

    if df.empty:
        st.info("🟡 Ledger empty. Run `python generator_daemon.py` (Option 2 to seed 50 benchmark transactions, or Option 1 for a single test event).")
        return

    # Metrics
    total_volume = df["amount_inr"].sum()
    failed_df = df[df["status"].isin(["PENDING_RETRY", "RECOVERED", "TERMINATED"])]
    at_risk_volume = failed_df["amount_inr"].sum()
    recovered_volume = df["recovered_amount"].sum()
    recovery_rate = (recovered_volume / at_risk_volume * 100) if at_risk_volume > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Ingested Volume", f"₹{total_volume:,.2f}")
    k2.metric("Revenue At Risk", f"₹{at_risk_volume:,.2f}")
    k3.metric("Revenue Won Back", f"₹{recovered_volume:,.2f}", delta=f"{recovery_rate:.1f}% Recovery")
    k4.metric("Transactions Handled", len(df), delta=f"{len(df[df['status'] == 'PENDING_RETRY'])} Active in Flight")

    st.divider()

    # Visualizations
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Transaction Lifecycle Status")
        fig_pie = px.pie(df, names="status", hole=0.5, color="status", color_discrete_map={
            "SUCCESS": "#3B82F6",
            "RECOVERED": "#10B981",
            "PENDING_RETRY": "#F59E0B",
            "TERMINATED": "#EF4444"
        })
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, width="stretch", key=f"pie_{len(df)}")

    with c2:
        st.subheader("Revenue Won Back by Category")
        if not failed_df.empty:
            cat_grp = failed_df.groupby("category")[["amount_inr", "recovered_amount"]].sum().reset_index()
            fig_bar = px.bar(
                cat_grp, x="category", y=["amount_inr", "recovered_amount"], barmode="group",
                color_discrete_sequence=["#94A3B8", "#10B981"]
            )
            fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), yaxis_title="Amount (₹)")
            st.plotly_chart(fig_bar, width="stretch", key=f"bar_{len(df)}")

    st.divider()

    # Full Data Table Stream
    st.subheader(f"📡 Live Transaction Stream ({len(df)} Records Ingested)")
    st.dataframe(
        df[["id", "customer_name", "category", "amount_inr", "status", "failure_reason", "recovered_amount", "created_at"]],
        width="stretch",
        hide_index=True
    )

    st.divider()

    # Segregated Download Section
    st.subheader("📊 Operational Escalation & Audit Exporter")
    exp_col1, exp_col2, exp_col3 = st.columns([2, 1, 1])
    with exp_col1:
        st.caption("Export structured CSVs for financial reconciliation and engineering escalations.")
    with exp_col2:
        st.download_button(
            label="📥 Download Chronological Audit CSV",
            data=build_chronological_csv(df).encode('utf-8'),
            file_name=f"Chronological_Audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch"
        )
    with exp_col3:
        st.download_button(
            label="🚨 Download Segregated Escalation Batch",
            data=build_escalation_csv(df).encode('utf-8'),
            file_name=f"Segregated_Escalation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch"
        )

    st.divider()

    # Real-Time Inspector with Filter & Limit Control
    st.subheader("🔍 Real-Time Audit & Voice Inspector")
    f_col1, f_col2 = st.columns([3, 1])
    with f_col1:
        search = st.text_input("Filter by ID, Customer Name, or Status", placeholder="e.g. TXN_20005, PENDING_RETRY, TERMINATED", key="search_bar")
    with f_col2:
        display_limit = st.selectbox("Show rows", options=[15, 30, 50, 100], index=2)

    filtered_df = df
    if search:
        filtered_df = df[
            df["id"].str.contains(search, case=False, na=False) |
            df["customer_name"].str.contains(search, case=False, na=False) |
            df["status"].str.contains(search, case=False, na=False)
        ]

    for _, row in filtered_df.head(display_limit).iterrows():
        status_emoji = "🟢" if row["status"] in ["SUCCESS", "RECOVERED"] else ("⏳" if row["status"] == "PENDING_RETRY" else "🔴")
        with st.expander(f"{status_emoji} {row['id']} | {row['customer_name']} | ₹{row['amount_inr']:,.2f} | Status: {row['status']}"):
            col_info, col_msg = st.columns(2)
            with col_info:
                st.write(f"**Category:** `{row['category']}` | **Initial Reason:** `{row['failure_reason']}`")
                if pd.notna(row["workflow_summary"]) and str(row["workflow_summary"]).strip().lower() not in ["none", "nan", ""]:
                    st.write(f"**Active Step:** `{row['workflow_summary']}`")
                if row["status"] == "PENDING_RETRY":
                    st.warning(f"⏳ **Next Execution Due:** `{row['next_attempt_at']}`")
                if pd.notna(row["promised_pay_date"]) and str(row["promised_pay_date"]).strip().lower() not in ["none", "nan", ""]:
                    st.info(f"📌 **PTP Registered Date:** {row['promised_pay_date']}")

            with col_msg:
                if pd.notna(row["hinglish_script"]) and str(row["hinglish_script"]).strip().lower() not in ["none", "nan", ""]:
                    st.success(f"🗣️ **Hinglish Message Sent:**\n\n{row['hinglish_script']}")
                if pd.notna(row["voice_audio_path"]) and row["voice_audio_path"] and os.path.exists(str(row["voice_audio_path"])):
                    st.caption("🔊 AI Hinglish Voice Note Generated:")
                    st.audio(str(row["voice_audio_path"]), format="audio/mp3")
            
            if pd.notna(row["audit_trail"]) and row["audit_trail"]:
                st.caption("Immutable Step-by-Step History:")
                try:
                    for log in json.loads(row["audit_trail"]):
                        st.code(log, language="bash")
                except Exception:
                    st.code(str(row["audit_trail"]), language="bash")

render_live_temporal_dashboard()