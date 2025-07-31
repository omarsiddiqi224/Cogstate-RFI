# Start from the Python 3.12.5 slim base image
FROM python:3.12.5-slim

# Set environment variables for non-interactive installs
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary system dependencies, OpenJDK 17, and other tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    git \
    openjdk-17-jdk \
    maven \
    wget \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install OpenJDK 8 manually
RUN mkdir -p /usr/lib/jvm && \
    cd /tmp && \
    wget https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u382-b05/OpenJDK8U-jdk_x64_linux_hotspot_8u382b05.tar.gz && \
    tar -xzf OpenJDK8U-jdk_x64_linux_hotspot_8u382b05.tar.gz -C /usr/lib/jvm && \
    mv /usr/lib/jvm/jdk8u382-b05 /usr/lib/jvm/java-8-openjdk-amd64 && \
    rm -rf /tmp/*

# Set JAVA_HOME to Java 17
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Update PATH
ENV PATH="$JAVA_HOME/bin:$PATH"

# Verify Java installations
RUN echo "Java 17 version:" && \
    java -version && \
    echo "Java 8 version:" && \
    /usr/lib/jvm/java-8-openjdk-amd64/bin/java -version

# Install Trivy
RUN wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add - && \
    echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" > /etc/apt/sources.list.d/trivy.list && \
    apt-get update && \
    apt-get install -y trivy && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for Trivy authentication
ENV TRIVY_USERNAME=djamel-touati-ust
ENV TRIVY_PASSWORD=REMOVEDNQexiZHspJlN4FvmdjhBPi6YHAVqTP3N9tgz
ENV TRIVY_AUTH_URL=ghcr.io

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies and Gunicorn using the single requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# (Optional) Update Trivy database
# RUN trivy image alpine

# Expose port 8000 for the main FastAPI app
EXPOSE 8000

# Set the entry point to run the FastAPI app with Gunicorn and Uvicorn workers
CMD ["gunicorn", "fast_api_v2:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "1800", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-"]