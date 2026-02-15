# Use a lightweight Python image
FROM python:3.10-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (matching your screenshots)
EXPOSE 8000

# Command to run the application using Gunicorn (production grade)
# Replace 'main:app' if your entry python file is named something else (e.g., 'run:app')
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]
