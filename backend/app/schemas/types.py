from typing import Annotated
from pydantic import Field
from app.core.config import MAX_TRANSACTION_AMOUNT, MIN_TRANSACTION_AMOUNT

# Whole Colombian pesos within the configured limits.
# Strict: only JSON integers are accepted, so a string like "50.000" (dot as thousands separator) is never read as 50.
AmountCOP = Annotated[int, Field(strict=True, ge=MIN_TRANSACTION_AMOUNT, le=MAX_TRANSACTION_AMOUNT)]
