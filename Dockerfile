# Stage 1: Build the Vue application
FROM node:22-alpine AS frontend-builder
WORKDIR /web-ui
COPY web-ui/package*.json ./
RUN npm install
COPY web-ui/ .
RUN npm run build

# Stage 2: Build the python environment with dependencies
FROM python:3.11-slim-bookworm AS builder

# Set environment variables to prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Create a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python Depend on virtual environment (Use domestic mirror sources to accelerate)
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# download only Playwright of Chromium Browser, system dependencies are installed in the next stage
RUN playwright install chromium

# Stage 3: Create the final, lean image
FROM python:3.11-slim-bookworm

# Set working directory and environment variables
WORKDIR /app
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
# Added environment variables to distinguishDockerenvironment and local environment
ENV RUNNING_IN_DOCKER=true
# inform Playwright where to find browser
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
# Set time zone to China time zone
ENV TZ=Asia/Shanghai

# from builder Stage a copy of the virtual environment so we can use playwright Order
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Install all system-level dependencies required to run the browser (includinglibzbar0）and network diagnostic tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tzdata \
        tini \
        libzbar0 \
        curl \
        wget \
        iputils-ping \
        dnsutils \
        iproute2 \
        netcat-openbsd \
        telnet \
    && playwright install-deps chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# from builder Staged copying of pre-downloaded browsers
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Copy the front-end build product to /app/dist
COPY --from=frontend-builder /web-ui/dist /app/dist

# Copy application code
# .dockerignore File handles exclusions-m
COPY . .

# Declare the port on which the service is running
EXPOSE 8000

# use tini as init，Responsible for recycling orphan child processes
ENTRYPOINT ["tini", "--"]

# Commands executed when the container starts
# How to start using the new architecture
CMD ["python", "-m", "src.app"]
