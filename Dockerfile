# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for imgkit and wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xvfb \
    && apt-get clean

# Create a non-root user with user ID 10014
RUN useradd -m -u 10014 appuser

# Set the non-root user as the owner of the working directory
RUN chown -R appuser /app

# Switch to the non-root user
USER 10014

# Copy the application requirements and install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY . .

# Copy Firebase service account key to the /firebase directory in the container
#COPY firebase/e-template-manager-firebase-adminsdk-fn65x-4fbc7ba929.json /firebase/e-template-manager-firebase-adminsdk-fn65x-4fbc7ba929.json

# Install python-dotenv if necessary to load environment variables from .env file
RUN pip install python-dotenv

# Expose the required port for Flask
EXPOSE 5000

# Run the app using Gunicorn (production WSGI server)
CMD ["gunicorn", "app:app"]