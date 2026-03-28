FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY main.py model.py model_loader.py project_config.py score.py validation.py ui.py ./
COPY config.yaml ./
COPY projects ./projects
COPY static ./static

RUN python -c "\
from project_config import get_project_dir; \
import json, pathlib; \
p = get_project_dir() / 'model.json'; \
assert p.exists() and p.stat().st_size > 0; \
d = json.loads(p.read_text(encoding='utf-8')); \
print(f'OK: {p}  (n_train={d.get(\"n_train\")}, version={d.get(\"version\", \"?\")})')"

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
