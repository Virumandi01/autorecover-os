from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class RecoveryCategory(str, Enum):
    PAYMENT_DEGRADATION = "PAYMENT_DEGRADATION"
    CHECKOUT_DROPOFF = "CHECKOUT_DROPOFF"
    FAILED_SUBSCRIPTION = "FAILED_SUBSCRIPTION"
    B2B_RECEIVABLES = "B2B_RECEIVABLES"
    MANDATE_RETRY = "MANDATE_RETRY"

class FailureReason(str, Enum):
    BANK_DOWNTIME = "BANK_DOWNTIME"
    PACKET_LOSS = "PACKET_LOSS"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    OTP_DROPOFF = "OTP_DROPOFF"
    EXPIRED_CARD = "EXPIRED_CARD"
    OVERDUE_INVOICE = "OVERDUE_INVOICE"
    MANDATE_REJECTED = "MANDATE_REJECTED"

class ActionType(str, Enum):
    SILENT_MANDATE_RETRY = "SILENT_MANDATE_RETRY"
    WHATSAPP_FAST_PAY = "WHATSAPP_FAST_PAY"
    HINGLISH_VOICE_NUDGE = "HINGLISH_VOICE_NUDGE"
    B2B_ESCALATION_EMAIL = "B2B_ESCALATION_EMAIL"
    PTP_LOGGED = "PTP_LOGGED"
    TERMINATE = "TERMINATE"

class PaymentEvent(BaseModel):
    transaction_id: str
    customer_id: str
    customer_name: str
    category: RecoveryCategory
    amount_inr: float
    channel: str
    failure_reason: FailureReason
    retry_count: int = 0
    days_overdue: int = 0
    is_salary_account: bool = False
    customer_opt_out: bool = False
    promised_pay_date: Optional[str] = None

class WorkflowStep(BaseModel):
    step_number: int
    scheduled_delay_minutes: int
    action: ActionType
    channel: str
    message_content: Optional[str] = None
    reason_context: str

class WorkflowDecision(BaseModel):
    category: RecoveryCategory
    primary_action: ActionType
    workflow_steps: List[WorkflowStep]
    root_cause_diagnosis: str
    hinglish_script: Optional[str] = None
    ptp_date_assigned: Optional[str] = None
    recovery_incentive_pct: float = Field(default=0.0, le=5.0)

class ExecutionTrace(BaseModel):
    transaction_id: str
    customer_name: str
    category: RecoveryCategory
    amount_at_risk: float
    failure_reason: FailureReason
    workflow_summary: str
    final_status: str
    recovered_amount: float
    steps_taken: int
    hinglish_log: Optional[str] = None
    ptp_status: Optional[str] = None
    audit_trail: List[str]