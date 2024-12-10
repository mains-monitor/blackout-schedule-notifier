# Use the latest Python Alpine-based image
FROM python:3.11-alpine

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python files and the downloader script
COPY src/*.py /app/
COPY downloader.sh /app/

# Install cron
RUN apk add --no-cache bash curl && \
    apk add --no-cache --virtual .build-deps gcc musl-dev && \
    apk add --no-cache cron && \
    chmod +x /app/downloader.sh

# Add crontab file in the cron directory
RUN echo "*/30 * * * * cd /app && /app/downloader.sh >> /var/log/cron.log 2>&1" > /etc/crontabs/root

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD ["crond", "-f", "-l", "2"]