FROM python:3.13.3-slim-bookworm

# Install dependencies for Playwright
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    curl \
    wget \
    gnupg \
    libgconf-2-4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    build-essential \
    python3-dev \
    libldap2-dev \
    libsasl2-dev \
    slapd \
    ldap-utils \
    tox \
    lcov \
    valgrind \
    # Cleanup to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install-deps
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Create directories for templates and schedules
RUN mkdir -p templates schedules layouts config

# Expose port
EXPOSE 8000

# Command to run the application
# DONT ACTIVATE MORE THAN ONE WORKER OR THINGS GET WEIRD
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--log-level=trace", "--access-logfile=-", "--error-logfile=-"]
