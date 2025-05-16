# Multi-stage build for full-stack application

# Frontend build stage
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Backend build stage
FROM python:3.11-slim AS backend-builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim
WORKDIR /app

# Copy backend
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=backend-builder /usr/local/bin/ /usr/local/bin/
COPY app/ ./app/

# Copy frontend build assets
COPY --from=frontend-builder /app/frontend/dist/ ./frontend/dist/

# Copy configuration files
COPY .env ./
COPY main.py ./

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"]
