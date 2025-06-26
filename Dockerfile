# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy source code to the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port used by Gunicorn
EXPOSE 8080

# Set the Cloud SQL instance connection name in DB_HOST
ENV DB_HOST="/cloudsql/vernal-shine-462108-t5:asia-south1:bookstore-data"

# Run the application using Gunicorn
CMD ["gunicorn", "-b", ":8080", "main:app"]
