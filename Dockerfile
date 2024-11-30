FROM python:3.13-slim

# Set working directory in container
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
COPY setup.py .

# Copy your source code
COPY src/ src/
COPY data/ data/

# Install dependencies and your package
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir .

# Command to run the application
CMD ["uvicorn", "mta_api.main:app", "--host", "0.0.0.0", "--port", "8000"]