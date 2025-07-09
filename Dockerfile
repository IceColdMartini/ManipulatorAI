# 1. Base Image
# Use an official Python runtime as a parent image. We use slim-buster for a smaller image size.
FROM python:3.11-slim

# 2. Set Environment Variables
# Prevents Python from writing pyc files to disc (equivalent to python -B)
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures that the python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# 3. Set Working Directory
# All subsequent commands will be run from this directory
WORKDIR /app

# 4. Install Dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Application Code
# Copy the source code into the container
COPY ./src /app/src

# 6. Expose Port
# The port the application will run on. This must match the port in the Uvicorn command.
EXPOSE 8000

# 7. Run Application
# Command to run the application using Uvicorn.
# --host 0.0.0.0 makes the server accessible from outside the container.
# --port 8000 is the port we exposed.
# --reload is great for development, as it automatically reloads the server on code changes.
# For production, you would typically remove --reload and use more workers.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
