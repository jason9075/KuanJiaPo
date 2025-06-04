FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    pkg-config \
    default-libmysqlclient-dev \
    gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["bash"]
