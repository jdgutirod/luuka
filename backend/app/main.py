import uvicorn

from fastapi import FastAPI
from app.core.config import PORT
# from app.routers import users, items

app = FastAPI(title="FastAPI App")

# app.include_router(users.router)
# app.include_router(items.router)

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