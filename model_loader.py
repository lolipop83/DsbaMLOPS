from __future__ import annotations

import json
import os
from pathlib import Path

from model import PriceModel
from project_config import get_project_dir


def load_model(project_name: str | None = None) -> PriceModel:
    env_path = os.getenv("MODEL_PATH")
    if env_path and project_name is None:
        path = Path(env_path)
    else:
        path = get_project_dir(project_name) / "model.json"

    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("version", "")
    return PriceModel(**data)
