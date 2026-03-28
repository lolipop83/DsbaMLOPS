from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriceModel:
    b0: float
    b_log_surface: float
    b_rooms: float
    sigma: float
    n_train: int
    type_local: str
    version: str = ""
