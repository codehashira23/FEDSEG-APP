FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    FEDSEG_INTERNAL_API_URL=http://127.0.0.1:8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Download model at build-time to embed inside the Docker image layer securely
# This completely eliminates 'download-on-boot' problems in Render free tier
RUN mkdir -p /app/model && gdown --id 1ao-ewYgWicBOQKCdtWYMsaq8Y-Wj_q2J -O /app/model/model.pt

COPY . .

RUN chmod +x docker/start-render.sh

EXPOSE 10000

CMD ["./docker/start-render.sh"]
