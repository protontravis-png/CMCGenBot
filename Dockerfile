# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy your project files into the container
COPY . .

# Install dependencies from requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port 80 if your app runs on it (optional, depending on your app setup)
# EXPOSE 80

# Command to run your app
CMD ["python", "main.py"]
