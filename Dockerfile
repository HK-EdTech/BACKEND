# Base image with Python 3.12
FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and activate a virtual environment:
#   1. We create a venv directory in /venv
#   2. We prepend /venv/bin to PATH so pip/python use that environment by default
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install system dependencies required for Prisma CLI (Node.js installation)
RUN apt-get update && \
    apt-get install -y libatomic1 openssl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install required python dependencies using the venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Generate Prisma client (required before using the client in the app)
RUN prisma generate

# Make the project root importable
ENV PYTHONPATH=/app

# Expose and launch
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]