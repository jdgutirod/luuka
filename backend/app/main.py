import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import CORS_ORIGINS, PORT
from app.core.exception_handlers import register_exception_handlers
from app.routers import accounts, group_charges, member_charges, transactions

app = FastAPI(title="FastAPI App")

# The token travels in the Authorization header, not in cookies, so credentials are not needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)

register_exception_handlers(app)

app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(group_charges.router)
app.include_router(member_charges.router)

@app.get("/health")
async def root() -> dict:
    """Health check endpoint."""
    return {"status": "FastAPI running"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
    )