# Dockerfile — ./gateway/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for faster rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy gateway code
COPY . .

# Expose the HTTP port
EXPOSE 8001

# Run Uvicorn on container start
CMD ["uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8001"]