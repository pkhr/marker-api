# Use Python 3.12 as the base image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the application using Gunicorn when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "10", "--worker-class", "gthread", "--worker-tmp-dir", "/dev/shm", "--max-requests", "100", "--max-requests-jitter", "50", "--timeout", "3600", "pdf2md:app"]
