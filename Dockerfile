FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Vendored build engine (html2pptx.js/build.js) — installed natively for
# this image's platform, not borrowed from a host checkout.
RUN npm install --prefix engine --omit=dev
RUN npx --prefix engine playwright install --with-deps chromium

RUN mkdir -p /app/data /app/engine/projects

EXPOSE 8501

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8501"]
