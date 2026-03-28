from __future__ import annotations

import math

from model import PriceModel


def predict_expected_price(model: PriceModel, surface: float, nb_room: int) -> float:
    log_price_hat = model.b0 + model.b_log_surface * math.log(surface) + model.b_rooms * nb_room
    return math.exp(log_price_hat)


def label_from_ratio(price_ratio: float, low: float = 0.9, high: float = 1.1) -> str:
    if price_ratio < low:
        return "underpriced"
    if price_ratio <= high:
        return "fair"
    return "overpriced"


def score_price(
    model: PriceModel,
    surface: float,
    nb_room: int,
    price: float,
    threshold_low: float = 0.9,
    threshold_high: float = 1.1,
) -> dict:
    expected = predict_expected_price(model, surface=surface, nb_room=nb_room)
    ratio = price / expected if expected > 0 else float("inf")
    z = (math.log(price) - math.log(expected)) / model.sigma if model.sigma > 0 else 0.0
    score = math.exp(-abs(z))

    return {
        "score": round(max(0.0, min(1.0, score)), 3),
        "expected_price": round(expected, 2),
        "price_ratio": round(ratio, 3),
        "label": label_from_ratio(ratio, threshold_low, threshold_high),
        "z": round(z, 3),
        "model_type_local": model.type_local,
        "model_n_train": model.n_train,
        "model_version": model.version,
    }
