# Builder stage
FROM python:3.13-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./user ./user
COPY ./alembic ./alembic
COPY alembic.ini .

# Final stage
FROM python:3.13-slim

WORKDIR /app

# Copy only installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy your app source code
COPY --from=builder /app /app

EXPOSE 8085

CMD ["bash", "-c", "alembic upgrade head && uvicorn user.main:app --host 0.0.0.0 --port 8085"]
