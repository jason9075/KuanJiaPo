FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r src/web_requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the application port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "8000"]
