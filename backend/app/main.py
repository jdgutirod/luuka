import uvicorn

from fastapi import FastAPI
from app.core.config import PORT
from app.core.exception_handlers import register_exception_handlers
from app.routers import accounts, transactions

app = FastAPI(title="FastAPI App")

register_exception_handlers(app)

app.include_router(accounts.router)
app.include_router(transactions.router)

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