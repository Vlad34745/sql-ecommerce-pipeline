FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY core ./core
COPY sql_queries ./sql_queries
COPY dashboard ./dashboard
COPY .env.example .
CMD ["python", "-m", "core.pipeline"]
