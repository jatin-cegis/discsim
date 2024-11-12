# Use the official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY api/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the API code
COPY api/ /app/api/

# Expose the API port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
