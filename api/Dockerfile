# Use the official Python image
FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    gfortran \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install project dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --default-timeout=1000 -r requirements.txt

# Copy the entire project into the container
COPY . .

# Install the project as a package
RUN pip install -e .

# Expose the API port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
