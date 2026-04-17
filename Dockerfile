# Use a stable Python image from Docker Hub (avoids the broken DO mirrors)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies for Postgres
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose the port Django will run on
EXPOSE 8000

# The command to run the app
CMD sh -c "python manage.py migrate --noinput && gunicorn matin.wsgi:application --bind 0.0.0.0:8000"