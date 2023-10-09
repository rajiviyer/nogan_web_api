# Use the python 3.10.13-bookworm container image
from python:3.10.13-bookworm

# Set the working directory to /app
WORKDIR /app

# Copy current directory contents into container at /app
ADD . /app

# Install the dependencies
RUN pip install -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=wsgi.py

# Run Gunicorn with your Flask application
CMD ["gunicorn", "-b", "0.0.0.0:5000", "wsgi:app"]