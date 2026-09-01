import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_FILE = "recovery_ledger.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        customer_name TEXT,
        category TEXT,
        amount_inr REAL,
        channel TEXT,
        status TEXT, -- 'SUCCESS', 'FAILED', 'RECOVERED', 'TERMINATED'
        failure_reason TEXT,
        retry_count INTEGER DEFAULT 0,
        days_overdue INTEGER DEFAULT 0,
        is_salary_account INTEGER DEFAULT 0,
        customer_opt_out INTEGER DEFAULT 0,
        promised_pay_date TEXT,
        recovered_amount REAL DEFAULT 0.0,
        workflow_summary TEXT,
        hinglish_script TEXT,
        audit_trail TEXT, -- JSON array of string logs
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def insert_transaction(txn: Dict[str, Any]):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO transactions (
        id, customer_name, category, amount_inr, channel, status,
        failure_reason, retry_count, days_overdue, is_salary_account,
        customer_opt_out, promised_pay_date, audit_trail, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        txn["id"], txn["customer_name"], txn["category"], txn["amount_inr"], txn["channel"],
        txn["status"], txn.get("failure_reason"), txn.get("retry_count", 0),
        txn.get("days_overdue", 0), 1 if txn.get("is_salary_account") else 0,
        1 if txn.get("customer_opt_out") else 0, txn.get("promised_pay_date"),
        json.dumps([f"Event ingested: {txn['status']} - {txn.get('failure_reason', 'SUCCESS')}"]),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_unprocessed_failed_events() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE status = 'FAILED'")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def update_recovery_trace(txn_id: str, status: str, recovered_amt: float, workflow_summary: str, hinglish: Optional[str], audit_trail: List[str]):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE transactions SET 
        status = ?,
        recovered_amount = ?,
        workflow_summary = ?,
        hinglish_script = ?,
        audit_trail = ?,
        processed_at = ?
    WHERE id = ?
    """, (
        status, recovered_amt, workflow_summary, hinglish,
        json.dumps(audit_trail), datetime.now().isoformat(), txn_id
    ))
    conn.commit()
    conn.close()