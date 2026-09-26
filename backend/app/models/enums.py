from enum import Enum

class ChargeState(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"


class TransactionType(str, Enum):
    RELOAD = "RELOAD"
    DIRECT_TRANSFER = "DIRECT_TRANSFER"
    COURT_PAYMENT = "COURT_PAYMENT"
