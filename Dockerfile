FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY config ./config
RUN pip install --no-cache-dir -e .
ENV ATLAS_CONFIG=/app/config/default.yaml
ENV ATLAS_DATA_DIR=/app/data
CMD ["python", "scripts/run_kraken_public.py", "--duration-sec", "60"]
