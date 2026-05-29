FROM python:3.11-slim

# poppler pour pdf2image
RUN apt-get update && apt-get install -y --no-install-recommends \
        poppler-utils \
        libjpeg-dev \
        zlib1g-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# Le port réel est fourni par $PORT (Render). start.sh fait migrations + bootstrap + uvicorn.
CMD ["sh", "start.sh"]
