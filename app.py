import time
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db import init_db, get_db, get_unprocessed_failed_events, update_recovery_trace
from engine.classifier import evaluate_bounded_workflow
from engine.executor import execute_bounded_workflow
from schemas import PaymentEvent, RecoveryCategory, FailureReason

st.set_page_config(page_title="AutoRecover OS | Payment Engine", page_icon="⚡", layout="wide")
init_db()

# --- BACKEND WORKER: INSTANT EVENT INGESTION & WORKFLOW DISPATCH ---
def process_incoming_queue():
    """Polls unhandled transactions and executes recovery workflows instantly."""
    pending = get_unprocessed_failed_events()
    for row in pending:
        try:
            ev = PaymentEvent(
                transaction_id=row["id"],
                customer_id=f"CUST_{row['id'][-4:]}",
                customer_name=row["customer_name"],
                category=RecoveryCategory(row["category"]),
                amount_inr=row["amount_inr"],
                channel=row["channel"],
                failure_reason=FailureReason(row["failure_reason"]) if row["failure_reason"] else FailureReason.PACKET_LOSS,
                retry_count=row["retry_count"],
                days_overdue=row["days_overdue"],
                is_salary_account=bool(row["is_salary_account"]),
                customer_opt_out=bool(row["customer_opt_out"]),
                promised_pay_date=row["promised_pay_date"]
            )
            decision = evaluate_bounded_workflow(ev)
            trace = execute_bounded_workflow(ev, decision)
            update_recovery_trace(
                txn_id=ev.transaction_id,
                status=trace.final_status,
                recovered_amt=trace.recovered_amount,
                workflow_summary=trace.workflow_summary,
                hinglish=trace.hinglish_log,
                audit_trail=trace.audit_trail
            )
        except Exception as e:
            print(f"Error processing transaction {row['id']}: {e}")

# Header
st.title("⚡ AutoRecover OS: Autonomous Payment Gateway Monitor")
st.caption("Active WebSocket / SQLite Event Bus • Real-Time Sub-Second Ingestion • Bounded Recovery Engine")

# --- REAL-TIME STREAMING COMPONENT (Runs every 1s automatically) ---
@st.fragment(run_every="1s")
def render_live_dashboard():
    # 1. Process any incoming events that arrived in the last second
    process_incoming_queue()

    # 2. Query updated database state
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY created_at DESC", conn)
    conn.close()

    if df.empty:
        st.info("🟡 Gateway listening for incoming transactions... Run `python generator_daemon.py` in Terminal 1 to stream events.")
        return

    # 3. Calculate Financial Metrics
    total_volume = df["amount_inr"].sum()
    failed_df = df[df["status"].isin(["FAILED", "RECOVERED", "UNRECOVERED", "TERMINATED"])]
    at_risk_volume = failed_df["amount_inr"].sum()
    recovered_volume = df["recovered_amount"].sum()
    recovery_rate = (recovered_volume / at_risk_volume * 100) if at_risk_volume > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Ingested Volume", f"₹{total_volume:,.2f}")
    k2.metric("Revenue At Risk (Failed)", f"₹{at_risk_volume:,.2f}")
    k3.metric("Revenue Won Back", f"₹{recovered_volume:,.2f}", delta=f"{recovery_rate:.1f}% Recovery")
    k4.metric("Total Transactions Handled", len(df))

    st.divider()

    # 4. Interactive Visualizations
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Transaction Status Breakdown")
        fig_pie = px.pie(df, names="status", hole=0.5, color="status", color_discrete_map={
            "SUCCESS": "#3B82F6",
            "RECOVERED": "#10B981",
            "FAILED": "#F59E0B",
            "UNRECOVERED": "#EF4444",
            "TERMINATED": "#6B7280"
        })
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, width="stretch", key=f"pie_{len(df)}")

    with c2:
        st.subheader("Recovery By Failure Category")
        if not failed_df.empty:
            cat_grp = failed_df.groupby("category")[["amount_inr", "recovered_amount"]].sum().reset_index()
            fig_bar = px.bar(
                cat_grp, x="category", y=["amount_inr", "recovered_amount"], barmode="group",
                color_discrete_sequence=["#94A3B8", "#10B981"]
            )
            fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), yaxis_title="Amount (₹)")
            st.plotly_chart(fig_bar, width="stretch", key=f"bar_{len(df)}")

    st.divider()

    # 5. Live Event Stream Table
    st.subheader("📡 Live Transaction Stream")
    st.dataframe(
        df[["id", "customer_name", "category", "amount_inr", "status", "failure_reason", "recovered_amount", "created_at"]].head(8),
        width="stretch",
        hide_index=True
    )

    # 6. Immutable Audit Trail Inspector
    st.subheader("🔍 Real-Time Audit & Workflow Inspector")
    search = st.text_input("Filter transactions by ID or Customer Name", placeholder="e.g. TXN_2005", key="search_bar")

    filtered_df = df
    if search:
        filtered_df = df[
            df["id"].str.contains(search, case=False, na=False) |
            df["customer_name"].str.contains(search, case=False, na=False)
        ]

    for _, row in filtered_df.head(10).iterrows():
        status_emoji = "🟢" if row["status"] in ["SUCCESS", "RECOVERED"] else ("🟡" if row["status"] == "FAILED" else "🔴")
        with st.expander(f"{status_emoji} {row['id']} | {row['customer_name']} | ₹{row['amount_inr']:,.2f} | Status: {row['status']}"):
            col_info, col_msg = st.columns(2)
            with col_info:
                st.write(f"**Category:** `{row['category']}`")
                if pd.notna(row["failure_reason"]) and str(row["failure_reason"]).strip().lower() not in ["none", "nan", ""]:
                    st.write(f"**Failure Reason:** `{row['failure_reason']}`")
                if pd.notna(row["workflow_summary"]) and str(row["workflow_summary"]).strip().lower() not in ["none", "nan", ""]:
                    st.write(f"**Workflow Executed:** `{row['workflow_summary']}`")
                if pd.notna(row["promised_pay_date"]) and str(row["promised_pay_date"]).strip().lower() not in ["none", "nan", ""]:
                    st.info(f"📌 **PTP Registered Date:** {row['promised_pay_date']}")
            with col_msg:
                if pd.notna(row["hinglish_script"]) and str(row["hinglish_script"]).strip().lower() not in ["none", "nan", ""]:
                    st.success(f"🗣️ **Hinglish Communication Sent:**\n\n{row['hinglish_script']}")
            
            if row["audit_trail"] and pd.notna(row["audit_trail"]):
                st.caption("Immutable Step-by-Step Audit Trail:")
                for log in json.loads(row["audit_trail"]):
                    st.code(log, language="bash")

render_live_dashboard()