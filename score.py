from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PriceModel:
    b0: float
    b_log_surface: float
    b_rooms: float
    sigma: float
    n_train: int
    type_local: str


def load_model() -> PriceModel:
    path = Path(os.getenv("MODEL_PATH", "artifacts/model.json"))
    data = json.loads(path.read_text(encoding="utf-8"))
    return PriceModel(**data)


_MODEL = load_model()


def predict_expected_price(surface: int, nb_room: int) -> float:
    log_price_hat = _MODEL.b0 + _MODEL.b_log_surface * math.log(surface) + _MODEL.b_rooms * nb_room
    return math.exp(log_price_hat)


def label_from_ratio(price_ratio: float) -> str:
    if price_ratio < 0.9:
        return "underpriced"
    if price_ratio <= 1.1:
        return "fair"
    return "overpriced"


def score_price(surface: int, nb_room: int, price: float) -> dict:
    expected = predict_expected_price(surface=surface, nb_room=nb_room)
    ratio = price / expected if expected > 0 else float("inf")
    z = (math.log(price) - math.log(expected)) / _MODEL.sigma
    score = math.exp(-abs(z))

    return {
        "score": round(max(0.0, min(1.0, score)), 3),
        "expected_price": round(expected, 2),
        "price_ratio": round(ratio, 3),
        "label": label_from_ratio(ratio),
        "z": round(z, 3),
        "model_type_local": _MODEL.type_local,
        "model_n_train": _MODEL.n_train,
    }