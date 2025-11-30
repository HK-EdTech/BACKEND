# Dockerfile
FROM python:3.12-slim

# Prevents Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG_TOKEN=super-secret-fake-debug-token

WORKDIR /app

# Install only dependencies first → better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actual code
COPY src ./src

# Run from the src folder
WORKDIR /app/src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]