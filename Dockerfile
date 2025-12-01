# Dockerfile
FROM python:3.12-slim

# Prevents Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Debug token (override with docker run -e or docker-compose)
# Ergo this DEBUG_TOKEN is no longer needed due to CI handling it in github action
# ENV DEBUG_TOKEN=super-secret-debug-token-123 

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# This is the magic line — makes the project root importable
ENV PYTHONPATH=/app

# Run uvicorn from the project root
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]