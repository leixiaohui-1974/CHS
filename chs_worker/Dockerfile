# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy both the worker and the SDK source code into the container
# The requirements.txt for the worker needs the SDK source to be present.
COPY ./chs_worker /app/chs_worker
COPY ./water_system_sdk /app/water_system_sdk

# Set the working directory to the worker's folder
WORKDIR /app/chs_worker

# Install any needed packages specified in requirements.txt
# This will install pika from PyPI and the local SDK from the copied source
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variables if needed (e.g., for RabbitMQ host)
# ENV RABBITMQ_HOST=rabbitmq

# Run main.py when the container launches
CMD ["python", "main.py"]
