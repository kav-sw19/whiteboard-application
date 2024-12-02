# Step 1: Use an official Python runtime as the base image
FROM python:3.9-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the application source code into the container
COPY . .

# Step 4: Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Expose the port used by the Flask application
EXPOSE 5000

# Step 6: Set the command to run the application
CMD ["python", "main.py"]
