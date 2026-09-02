import os
import json
import random
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.express as px
from db import init_db, get_db, get_due_recovery_jobs, schedule_next_retry, finalize_transaction
from engine.classifier import evaluate_bounded_workflow
from engine.dispatcher import synthesize_hinglish_voice, send_real_whatsapp_interactive
from schemas import PaymentEvent, RecoveryCategory, FailureReason

st.set_page_config(page_title="AutoRecover OS | Temporal Engine", page_icon="⚡", layout="wide")
init_db()

# --- TEMPORAL STATE MACHINE WORKER ---
def run_temporal_recovery_worker():
    """
    Time Compression Engine:
    1 scheduled workflow minute = 1 real-world second.
    E.g. 5 min checkout delay = 5 real seconds.
    90 min bank degradation delay = 12 real seconds.
    """
    due_jobs = get_due_recovery_jobs()
    for row in due_jobs:
        txn_id = row["id"]
        step = row["current_step"] + 1
        
        # Build event model
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
                f"🛑 [{datetime.now().strftime('%H:%M:%S')}] Compliance Stop: Max retries ({row['max_steps']}) reached or customer opted out."
            )
            continue

        # Determine delay (Scaled to seconds for live demo)
        target_step = decision.workflow_steps[min(step - 1, len(decision.workflow_steps) - 1)]
        scaled_delay_sec = max(3, int(target_step.scheduled_delay_minutes / 10)) if target_step.scheduled_delay_minutes > 0 else 4
        next_eta = (datetime.now() + timedelta(seconds=scaled_delay_sec)).isoformat()

        # Generate Audio & Send WhatsApp if communication action
        audio_path = row.get("voice_audio_path")
        hinglish_msg = decision.hinglish_script
        if hinglish_msg and not audio_path:
            audio_path = synthesize_hinglish_voice(hinglish_msg, txn_id)
            send_real_whatsapp_interactive(
                row.get("customer_phone", "+919876543210"),
                row["customer_name"],
                row["amount_inr"],
                f"https://rzp.io/l/{txn_id.lower()}",
                hinglish_msg
            )

        # 65% probability of recovery at current step
        is_recovered = random.random() < 0.65
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
                log_entry=f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Step {step} Failed ({target_step.action.value}). Scheduled Step {step + 1} retry in {scaled_delay_sec}s.",
                summary=f"{target_step.action.value} (Step {step}/{row['max_steps']})",
                hinglish=hinglish_msg,
                audio_path=audio_path
            )

# Header
st.title("⚡ AutoRecover OS: Temporal Recovery & Voice OS")
st.caption("Temporal State Machine • Multi-Stage Delayed Backoff • Microsoft Neural Hinglish Voice Synthesis • WhatsApp Interactive Integration")

# --- REAL-TIME STREAMING FRAGMENT (Polls every 1s) ---
@st.fragment(run_every="1s")
def render_live_temporal_dashboard():
    # 1. Execute state machine steps for any due jobs
    run_temporal_recovery_worker()

    # 2. Fetch latest data
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY created_at DESC", conn)
    conn.close()

    if df.empty:
        st.info("Gateway listening. Run `python generator_daemon.py` in Terminal 2 to stream events.")
        return

    # 3. Top Metrics
    total_volume = df["amount_inr"].sum()
    failed_df = df[df["status"].isin(["PENDING_RETRY", "RECOVERED", "TERMINATED"])]
    at_risk_volume = failed_df["amount_inr"].sum()
    recovered_volume = df["recovered_amount"].sum()
    recovery_rate = (recovered_volume / at_risk_volume * 100) if at_risk_volume > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Ingested Volume", f"₹{total_volume:,.2f}")
    k2.metric("Revenue At Risk", f"₹{at_risk_volume:,.2f}")
    k3.metric("Revenue Won Back", f"₹{recovered_volume:,.2f}", delta=f"{recovery_rate:.1f}% Recovery")
    k4.metric("Active Workflows in Flight", len(df[df["status"] == "PENDING_RETRY"]))

    st.divider()

    # 4. Charts
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
        st.subheader("Revenue Won Back By Category")
        if not failed_df.empty:
            cat_grp = failed_df.groupby("category")[["amount_inr", "recovered_amount"]].sum().reset_index()
            fig_bar = px.bar(
                cat_grp, x="category", y=["amount_inr", "recovered_amount"], barmode="group",
                color_discrete_sequence=["#94A3B8", "#10B981"]
            )
            fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), yaxis_title="Amount (₹)")
            st.plotly_chart(fig_bar, width="stretch", key=f"bar_{len(df)}")

    st.divider()

    # 5. Live State Machine Inspector with Voice Audio Player
    st.subheader("🔍 Live Temporal Inspector & Hinglish Voice Player")
    search = st.text_input("Filter by ID, Customer Name, or Status", placeholder="e.g. TXN_2005", key="search_bar")

    filtered_df = df
    if search:
        filtered_df = df[
            df["id"].str.contains(search, case=False, na=False) |
            df["customer_name"].str.contains(search, case=False, na=False) |
            df["status"].str.contains(search, case=False, na=False)
        ]

    for _, row in filtered_df.head(10).iterrows():
        status_emoji = "🟢" if row["status"] in ["SUCCESS", "RECOVERED"] else ("⏳" if row["status"] == "PENDING_RETRY" else "🔴")
        with st.expander(f"{status_emoji} {row['id']} | {row['customer_name']} | ₹{row['amount_inr']:,.2f} | Status: {row['status']}"):
            col_info, col_msg = st.columns(2)
            with col_info:
                st.write(f"**Category:** `{row['category']}` | **Failure Reason:** `{row['failure_reason']}`")
                if pd.notna(row["workflow_summary"]) and str(row["workflow_summary"]).strip().lower() not in ["none", "nan", ""]:
                    st.write(f"**Active Step:** `{row['workflow_summary']}`")
                if row["status"] == "PENDING_RETRY":
                    st.warning(f"⏳ **Next Execution Due:** `{row['next_attempt_at']}`")
                if pd.notna(row["promised_pay_date"]) and str(row["promised_pay_date"]).strip().lower() not in ["none", "nan", ""]:
                    st.info(f"📌 **PTP Registered Date:** {row['promised_pay_date']}")

            with col_msg:
                if pd.notna(row["hinglish_script"]) and str(row["hinglish_script"]).strip().lower() not in ["none", "nan", ""]:
                    st.success(f"🗣️ **Hinglish Message:**\n\n{row['hinglish_script']}")
                if pd.notna(row["voice_audio_path"]) and row["voice_audio_path"] and os.path.exists(str(row["voice_audio_path"])):
                    st.caption("🔊 AI Hinglish Voice Note Generated:")
                    st.audio(str(row["voice_audio_path"]), format="audio/mp3")
            
            if pd.notna(row["audit_trail"]) and row["audit_trail"]:
                st.caption("Immutable Temporal Audit Trail:")
                try:
                    for log in json.loads(row["audit_trail"]):
                        st.code(log, language="bash")
                except Exception:
                    st.code(str(row["audit_trail"]), language="bash")

# Correct matching call to start the fragment
render_live_temporal_dashboard()