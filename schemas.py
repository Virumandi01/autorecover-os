from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class FailureReason(str, Enum):
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    BANK_DOWNTIME = "BANK_DOWNTIME"
    EXPIRED_CARD = "EXPIRED_CARD"
    OTP_TIMEOUT = "OTP_TIMEOUT"
    MANDATE_REJECTED = "MANDATE_REJECTED"
    USER_ABANDONED = "USER_ABANDONED"

class PaymentChannel(str, Enum):
    UPI = "UPI"
    CARD = "CARD"
    MANDATE = "MANDATE"
    NETBANKING = "NETBANKING"

class ActionType(str, Enum):
    SILENT_RETRY = "SILENT_RETRY"
    WHATSAPP_PAY_LINK = "WHATSAPP_PAY_LINK"
    EMAIL_INVOICE = "EMAIL_INVOICE"
    TERMINATE = "TERMINATE"

class PaymentEvent(BaseModel):
    transaction_id: str
    customer_id: str
    customer_name: str
    amount_inr: float
    channel: PaymentChannel
    failure_reason: FailureReason
    retry_count: int = 0
    is_salary_account: bool = False
    customer_opt_out: bool = False

class AgentDecision(BaseModel):
    action: ActionType
    target_channel: str
    scheduled_hour_delay: int = Field(
        description="Hours to delay before execution (e.g. 0 for immediate, 24 for next day)"
    )
    rationale: str = Field(description="Max 15 words explaining root-cause diagnosis")
    incentive_discount_pct: float = Field(default=0.0, le=5.0)

class RecoveryResult(BaseModel):
    transaction_id: str
    initial_amount: float
    action_taken: ActionType
    recovered: bool
    amount_recovered: float
    audit_note: str