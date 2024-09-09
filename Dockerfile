# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Firebase credentials into the container
COPY e-template-manager-firebase-adminsdk-fn65x-75d0253fa3.json /app/

# Copy the rest of the application code into the container
COPY . .

# Expose port 8080 for the Gunicorn server
EXPOSE 8080

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
