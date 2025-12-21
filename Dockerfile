# APT - Allied Performance Testing - Docker Image
# Includes: Python, Playwright, k6, JMeter, and all dependencies

FROM python:3.11-slim

LABEL maintainer="APT - Allied Performance Testing"
LABEL description="APT: Allied tools, unified performance - Complete framework with Playwright, k6, and JMeter"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    unzip \
    ca-certificates \
    gnupg \
    openjdk-11-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install k6
RUN gpg -k && \
    gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
    --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69 && \
    echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
    tee /etc/apt/sources.list.d/k6.list && \
    apt-get update && \
    apt-get install -y k6 && \
    rm -rf /var/lib/apt/lists/*

# Install JMeter
ENV JMETER_VERSION=5.6.3
ENV JMETER_HOME=/opt/apache-jmeter-${JMETER_VERSION}
ENV PATH=${JMETER_HOME}/bin:${PATH}

RUN wget https://dlcdn.apache.org/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz && \
    tar -xzf apache-jmeter-${JMETER_VERSION}.tgz -C /opt && \
    rm apache-jmeter-${JMETER_VERSION}.tgz

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy framework code
COPY performance/ ./performance/
COPY tests/ ./tests/
COPY config/ ./config/
COPY pytest.ini .
COPY setup.py .

# Install framework as package
RUN pip install -e .

# Create directories for results
RUN mkdir -p /app/performance_results /app/logs

# Set permissions
RUN chmod -R 755 /app

# Default command
CMD ["pytest", "--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import playwright; import aiohttp; print('OK')" || exit 1
