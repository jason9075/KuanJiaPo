FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for MySQL client
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    gcc \
    && apt-get clean

# Copy application files
COPY src /app/src

# Install dependencies
RUN pip install --no-cache-dir -r src/web_requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the application port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "8000"]
