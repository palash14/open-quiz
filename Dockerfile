FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OAUTHLIB_INSECURE_TRANSPORT=1 \
    PYTHONPATH=/app \
    APP_ENVIRONMENT=development

# Create working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Fix permissions
# RUN addgroup --system appgroup && \
# adduser --system --ingroup appgroup appuser && \
# chown -R appuser:appgroup /app

# Expose the application port
EXPOSE 8000

# Switch to non-root user
# USER appuser

# Set default command to run FastAPI app with autoreload
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
