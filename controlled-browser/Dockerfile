# Minimalistic Dockerfile for Chrome automation test
FROM python:3.11-alpine

# Install Chromium and dependencies
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && find /usr/local -type d -name __pycache__ -exec rm -r {} + \
    && find /usr/local -type f -name '*.pyc' -delete \
    && find /usr/local -type f -name '*.pyo' -delete

# Copy test script
COPY test_schedule_extractor.py .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables for Chromium
ENV CHROME_BIN=/usr/bin/chromium-browser \
    CHROME_PATH=/usr/lib/chromium/ \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Run the test
CMD ["python", "test_schedule_extractor.py"]
