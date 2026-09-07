FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# build-essential is needed when a Python dependency has no pre-built wheel.
# Install Debian's architecture-native 7zz. api_7z.py otherwise downloads an
# x86_64-only binary at runtime, which breaks on Apple Silicon/ARM64 containers.
# xz-utils stays as a fallback for the project's legacy downloader.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        7zip \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

EXPOSE 5000 5010 5020 5030 5040

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "600", "Z_SERVER:SERVER"]
