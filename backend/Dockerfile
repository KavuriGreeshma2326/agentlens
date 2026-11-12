FROM python:3.12-slim

# Don't write .pyc files and ensure stdout/stderr are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Run migrations then start Uvicorn.
# Uvicorn is started with --host 0.0.0.0 so it's reachable from outside the container.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
