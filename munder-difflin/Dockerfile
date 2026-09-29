FROM node:20-bookworm-slim

# Hindari interaksi prompt saat apt-get
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install toolchain compile (C++, Python) dan dependensi GUI Chromium/Electron
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3 \
    make \
    g++ \
    curl \
    ca-certificates \
    openssh-client \
    # Display Server virtual & Window Manager
    xvfb \
    openbox \
    x11vnc \
    novnc \
    websockify \
    # Dependensi runtime Chromium / Electron
    libnss3 \
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
    libcairo2 \
    libxshmfence1 \
    libglu1-mesa \
    libgtk-3-0 \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

# Buat direktori kerja
WORKDIR /app

# 2. Clone repositori Munder Difflin
RUN git clone https://github.com/chaitanyagiri/munder-difflin.git .

# 3. Install dependensi dan rebuild native addon untuk Electron ABI
RUN npm install

# 4. Build bundle frontend dan backend
RUN npm run build

# Siapkan entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port noVNC
EXPOSE 6080

ENTRYPOINT ["/entrypoint.sh"]
