# Use the official Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python scripts into the container
COPY . .

# Start all three consumers in parallel
CMD ["sh", "-c", "python run_vectorizer.py"]
