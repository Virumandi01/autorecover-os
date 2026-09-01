import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from generator import generate_full_scenario_events
from engine.classifier import evaluate_bounded_workflow
from engine.executor import execute_bounded_workflow

st.set_page_config(page_title="AutoRecover OS | Razorpay AI", page_icon="⚡", layout="wide")

st.title("⚡ AutoRecover OS: AI Revenue Recovery Engine")
st.caption("Autonomous, bounded revenue recovery covering all 7 Razorpay hackathon tracks.")

# Sidebar Filters & Trigger
st.sidebar.header("Batch Orchestrator")
batch_size = st.sidebar.slider("Ingestion Batch Size", min_value=10, max_value=100, value=50, step=10)
selected_cat = st.sidebar.selectbox("Filter Category", ["ALL"] + [
    "PAYMENT_DEGRADATION", "CHECKOUT_DROPOFF", "FAILED_SUBSCRIPTION", "B2B_RECEIVABLES", "MANDATE_RETRY"
])
run_btn = st.sidebar.button("Run Batch Pipeline", type="primary")

if "full_traces" not in st.session_state or run_btn:
    with st.spinner("Ingesting transactions and executing 7-track bounded recovery matrix..."):
        events = generate_full_scenario_events(batch_size)
        traces = []
        for ev in events:
            decision = evaluate_bounded_workflow(ev)
            trace = execute_bounded_workflow(ev, decision)
            traces.append(trace)
        st.session_state.full_traces = traces

traces = st.session_state.full_traces
if selected_cat != "ALL":
    traces = [t for t in traces if t.category.value == selected_cat]

# Top Financial KPIs
total_at_risk = sum(t.amount_at_risk for t in traces)
total_recovered = sum(t.recovered_amount for t in traces)
recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0
total_success = sum(1 for t in traces if t.final_status == "RECOVERED")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue At Risk", f"₹{total_at_risk:,.2f}")
col2.metric("Money Recovered", f"₹{total_recovered:,.2f}", delta=f"{recovery_rate:.1f}% Recovery Rate")
col3.metric("Successful Recoveries", f"{total_success} / {len(traces)}")
col4.metric("Active PTP Trackers", f"{sum(1 for t in traces if t.ptp_status)}")

st.divider()

# Visualization Columns
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 Recovery Split by Problem Track")
    df_cat = pd.DataFrame([
        {
            "Category": t.category.value.replace("_", " "),
            "At Risk": t.amount_at_risk,
            "Recovered": t.recovered_amount
        } for t in traces
    ])
    if not df_cat.empty:
        grouped = df_cat.groupby("Category").sum().reset_index()
        fig_bar = px.bar(
            grouped, x="Category", y=["At Risk", "Recovered"],
            barmode="group",
            color_discrete_sequence=["#94A3B8", "#10B981"]
        )
        fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), yaxis_title="Amount (₹)")
        st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.subheader("💰 Overall Win/Loss Ratio")
    fig_donut = go.Figure(data=[go.Pie(
        labels=["Recovered", "Unrecovered / Terminated"],
        values=[total_recovered, max(0.0, total_at_risk - total_recovered)],
        hole=0.55,
        marker_colors=["#10B981", "#EF4444"]
    )])
    fig_donut.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig_donut, use_container_width=True)

st.divider()

# Audit Logs & Hinglish/PTP Inspector
st.subheader("📋 Bounded Audit Trail & Agent Interventions")
search = st.text_input("Search by Transaction ID or Customer Name", placeholder="e.g. TXN_2005 or Aarav")

for t in traces:
    if search.lower() in t.transaction_id.lower() or search.lower() in t.customer_name.lower():
        icon = "🟢" if t.final_status == "RECOVERED" else "🔴"
        with st.expander(f"{icon} {t.transaction_id} — {t.customer_name} | {t.category.value} | At Risk: ₹{t.amount_at_risk:,.2f} | Status: {t.final_status}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Action Executed:** `{t.workflow_summary}`")
                st.markdown(f"**Amount Won Back:** `₹{t.recovered_amount:,.2f}`")
                if t.ptp_status:
                    st.info(f"📌 **Promise-to-Pay Tracker:** {t.ptp_status}")
            with col_b:
                if t.hinglish_log:
                    st.success(f"🗣️ **Hinglish Voice/WhatsApp Script:**\n\n_{t.hinglish_log}_")
            
            st.markdown("**Step-by-Step Immutable Audit Log:**")
            for step in t.audit_trail:
                st.code(step, language="bash")