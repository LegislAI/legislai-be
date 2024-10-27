FROM public.ecr.aws/sam/build-python3.12:latest

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt to the working directory
COPY requirements.txt .

# Install dependencies
RUN echo "Installing dependencies..." && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . ./Authorization

# Set environment variable for app name (if needed)
ARG app_name
ENV APP_NAME=${app_name}

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "Authorization.api:app", "--host", "0.0.0.0", "--port", "8000"]
