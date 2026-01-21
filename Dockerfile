# Base image
FROM python:3.9-slim

# Install utilities and Chrome dependencies
# We install busybox, curl, unzip, and libraries needed for Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    libgconf-2-4 \
    libxss1 \
    libnss3 \
    libappindicator1 \
    libindicator7 \
    fonts-liberation \
    libasound2 \
    libnspr4 \
    libx11-xcb1 \
    libxtst6 \
    xdg-utils \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
# Note: We use a fixed version or latest stable. 
# For simplicity in this template, we fetch the latest stable google-chrome-stable
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy App Code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
