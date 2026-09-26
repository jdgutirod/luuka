FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first, so they are cached while only the code changes
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# Do not run the API as root
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Creates the missing tables and starts the API
CMD ["sh", "-c", "python -m app.db.init_db && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
