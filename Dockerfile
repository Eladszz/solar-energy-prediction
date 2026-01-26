# Multi-stage build for Solar Energy Prediction Application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY solar_backend/backend_requirements.txt /app/backend_requirements.txt
COPY solar_ui/frontend_requirements.txt /app/frontend_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend_requirements.txt
RUN pip install --no-cache-dir -r frontend_requirements.txt

# Copy application code
COPY solar_backend /app/solar_backend
COPY solar_ui /app/solar_ui

# Create logs directory
RUN mkdir -p /app/solar_backend/logs

# Expose ports
# 8000 for FastAPI backend
# 8501 for Streamlit frontend
EXPOSE 8000 8501

# Create startup script
RUN echo '#!/bin/bash\n\
cd /app/solar_backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &\n\
cd /app/solar_ui && streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &\n\
wait' > /app/start.sh && chmod +x /app/start.sh

# Run both services
CMD ["/app/start.sh"]
