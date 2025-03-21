# Use the official Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python scripts into the container
COPY . .

ARG RUN_ARG
ENV RUN_ARG=${RUN_ARG}

# Start all three consumers in parallel
CMD ["sh", "-c", "python run.py --${RUN_ARG}"]
