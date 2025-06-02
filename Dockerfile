FROM python:3.13-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Expose the port your FastAPI app listens on
EXPOSE 8085

# Run FastAPI app with Uvicorn
CMD ["bash", "-c", "alembic upgrade head && uvicorn user.main:app --host 0.0.0.0 --port 8085"]
