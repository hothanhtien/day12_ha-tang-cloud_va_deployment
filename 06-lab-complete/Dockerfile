# ============================================================
# Production Dockerfile — Single-stage, non-root
# (Đơn giản hóa từ multi-stage gốc để tránh bug copy site-packages)
# ============================================================

FROM python:3.11-slim

# Cài gcc cho một số package cần build (vd psutil)
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Tạo user non-root
RUN groupadd -r agent && useradd -r -g agent -d /app agent

WORKDIR /app

# Cài dependencies vào /usr/local (site-packages chuẩn của Python)
COPY 06-lab-complete/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y gcc && apt-get autoremove -y

# Copy source code
COPY 06-lab-complete/app/ ./app/
COPY utils/ ./utils/

# Set quyền cho user agent
RUN chown -R agent:agent /app

USER agent

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
