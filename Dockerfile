# Use official slim Python image for smaller footprint
FROM python:3.11-slim

# working directory inside container
WORKDIR /app

# install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# copy requirement file first so that docker layer cache is effective
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app sources
COPY . .

# create instance directory (used by the application)
RUN mkdir -p instance

# expose port that Fly.io (and local testing) will use
EXPOSE 8080

# start the application with gunicorn
# keep a single worker for low-memory Fly machines
CMD ["gunicorn", "--workers", "1", "--worker-class", "gthread", "--threads", "2", "--timeout", "120", "--graceful-timeout", "30", "--worker-tmp-dir", "/dev/shm", "-b", "0.0.0.0:8080", "app:create_app()"]
