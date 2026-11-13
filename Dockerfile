# 1. Base Image: Official slim Python 3.12 on Linux
FROM python:3.12-slim

# 2. Set working directory inside the container
WORKDIR /app

# 3. Prevent Python from buffering stdout/stderr and writing .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 4. Install essential OS curl/certificates for secure package downloads
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 5. Layer Caching: Install Python dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Install Playwright Chromium and required Linux system libraries
RUN playwright install --with-deps chromium

# 7. Copy remaining test automation code into the container
COPY . .

# 8. Default Execution: Run login smoke test suite
CMD ["pytest", "-m", "smoke", "-v", "--tb=short", "-o", "log_cli=false"]
