import sqlite3
import json
from datetime import datetime, timedelta
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
        customer_phone TEXT,
        category TEXT,
        amount_inr REAL,
        channel TEXT,
        status TEXT, -- 'PENDING_RETRY', 'SUCCESS', 'RECOVERED', 'TERMINATED'
        failure_reason TEXT,
        current_step INTEGER DEFAULT 0,
        max_steps INTEGER DEFAULT 3,
        next_attempt_at TIMESTAMP,
        days_overdue INTEGER DEFAULT 0,
        is_salary_account INTEGER DEFAULT 0,
        customer_opt_out INTEGER DEFAULT 0,
        promised_pay_date TEXT,
        recovered_amount REAL DEFAULT 0.0,
        workflow_summary TEXT,
        hinglish_script TEXT,
        voice_audio_path TEXT,
        audit_trail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated_at TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def insert_transaction(txn: Dict[str, Any]):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO transactions (
        id, customer_name, customer_phone, category, amount_inr, channel, status,
        failure_reason, current_step, max_steps, next_attempt_at, days_overdue, 
        is_salary_account, customer_opt_out, promised_pay_date, audit_trail, created_at, last_updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        txn["id"], txn["customer_name"], txn.get("customer_phone", "+919876543210"), 
        txn["category"], txn["amount_inr"], txn["channel"], txn["status"], 
        txn.get("failure_reason"), 0, 3, datetime.now().isoformat(),
        txn.get("days_overdue", 0), 1 if txn.get("is_salary_account") else 0,
        1 if txn.get("customer_opt_out") else 0, txn.get("promised_pay_date"),
        json.dumps([f"[{datetime.now().strftime('%H:%M:%S')}] Ingested: {txn['status']} ({txn.get('failure_reason', 'OK')})"]),
        datetime.now().isoformat(), datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_due_recovery_jobs() -> List[Dict[str, Any]]:
    """Fetches transactions whose scheduled next_attempt_at is <= NOW."""
    conn = get_db()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    cursor.execute("""
        SELECT * FROM transactions 
        WHERE status = 'PENDING_RETRY' AND next_attempt_at <= ?
    """, (now_iso,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def schedule_next_retry(txn_id: str, next_attempt_at: str, step_num: int, log_entry: str, summary: str, hinglish: Optional[str] = None, audio_path: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT audit_trail FROM transactions WHERE id = ?", (txn_id,))
    row = cursor.fetchone()
    logs = json.loads(row["audit_trail"]) if row and row["audit_trail"] else []
    logs.append(log_entry)

    cursor.execute("""
    UPDATE transactions SET 
        current_step = ?,
        next_attempt_at = ?,
        workflow_summary = ?,
        hinglish_script = COALESCE(?, hinglish_script),
        voice_audio_path = COALESCE(?, voice_audio_path),
        audit_trail = ?,
        last_updated_at = ?
    WHERE id = ?
    """, (step_num, next_attempt_at, summary, hinglish, audio_path, json.dumps(logs), datetime.now().isoformat(), txn_id))
    conn.commit()
    conn.close()

def finalize_transaction(txn_id: str, final_status: str, recovered_amt: float, log_entry: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT audit_trail FROM transactions WHERE id = ?", (txn_id,))
    row = cursor.fetchone()
    logs = json.loads(row["audit_trail"]) if row and row["audit_trail"] else []
    logs.append(log_entry)

    cursor.execute("""
    UPDATE transactions SET 
        status = ?,
        recovered_amount = ?,
        audit_trail = ?,
        last_updated_at = ?
    WHERE id = ?
    """, (final_status, recovered_amt, json.dumps(logs), datetime.now().isoformat(), txn_id))
    conn.commit()
    conn.close()

# In db.py, add this function at the bottom:
def clear_all_transactions():
    """Wipes all transaction rows safely without file locking issues."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()