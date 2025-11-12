# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only requirements first (for efficient caching)
COPY requirements.txt .

# Upgrade pip & install dependencies
RUN pip install --no-cache-dir --no-deps -r requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install torch transformers accelerate
RUN pip install --no-cache-dir -r requirements.txt


# Copy rest of the backend files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
