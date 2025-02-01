FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including libGL)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean

# Copy application files
COPY src /app/src

# Install dependencies
RUN pip install --no-cache-dir -r src/detect_requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1


# Command to run the detection script
CMD ["python", "detect.py"]
