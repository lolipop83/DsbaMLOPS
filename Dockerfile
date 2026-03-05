FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY main.py score.py validation.py README.md ./
COPY artifacts/model.json ./artifacts/model.json
COPY static ./static

ENV MODEL_PATH=/app/artifacts/model.json

RUN python -c "import json, pathlib; p=pathlib.Path('/app/artifacts/model.json'); assert p.exists() and p.stat().st_size>0; json.loads(p.read_text(encoding='utf-8'))"

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]