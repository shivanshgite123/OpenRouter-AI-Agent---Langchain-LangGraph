FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000
ENV STREAMLIT_PORT=8501
ENV BACKEND_URL=http://localhost:8000

EXPOSE 8000
EXPOSE 8501

CMD ["sh", "-c", "uvicorn backend.main:app --host $BACKEND_HOST --port $BACKEND_PORT & streamlit run app.py --server.address 0.0.0.0 --server.port $STREAMLIT_PORT"]