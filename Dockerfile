# Use a slim Python image (adjust version as needed)
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install OS-level dependencies (build tools for numpy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy app code
COPY . .

# Expose Streamlit on port 8000
EXPOSE 8000

# Set the entrypoint
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
