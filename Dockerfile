# Use the slim version of the Ubuntu image
FROM python:3.12-slim

# Set environment variables to non-interactive
ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-get install -y cron tesseract-ocr curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install requirements using pip
RUN python3.12 -m ensurepip && \
    python3.12 -m pip install -r requirements.txt

# Copy the downloader script, entrypoint script, and python sources to the container
COPY src /app/src
COPY downloader.sh /app/downloader.sh
COPY entrypoint.sh /app/entrypoint.sh

# Give execution rights to the scripts
RUN chmod +x /app/downloader.sh /app/entrypoint.sh

# Add cron job to run downloader.sh every 30 minutes
RUN echo "*/30 * * * * cd /app && /app/downloader.sh > /proc/1/fd/1 2>&1" >> /etc/crontab
RUN chmod 0644 /etc/crontab
RUN crontab /etc/crontab

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# # Start cron service
# CMD ["cron", "-f", "-l", "2"]