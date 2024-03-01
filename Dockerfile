# Use the official Python image as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run Gunicorn with your WSGI app (main.py) when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
