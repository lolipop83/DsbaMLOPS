# train_model.py
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PriceModel:
    b0: float
    b_log_surface: float
    b_rooms: float
    sigma: float
    n_train: int
    type_local: str


def _mad_sigma(residuals: np.ndarray) -> float:
    med = np.median(residuals)
    mad = np.median(np.abs(residuals - med))
    return float(1.4826 * mad)


def train_model(csv_path: str, out_path: str) -> PriceModel:
    df = pd.read_csv(csv_path, sep=";")

    df["type_local"] = df["type_local"].astype(str)
    df = df[df["type_local"] == "Appartement"]

    for col in ["valeur_fonciere", "surface_reelle_bati", "nombre_pieces_principales"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati", "nombre_pieces_principales"])
    df = df[(df["valeur_fonciere"] > 1000) & (df["surface_reelle_bati"] > 5)]
    df = df[df["nombre_pieces_principales"] > 0]

    if len(df) < 30:
        raise ValueError(f"Not enough rows after filtering to Appartement only: n={len(df)}")

    y = np.log(df["valeur_fonciere"].to_numpy(dtype=float))
    x_surface = np.log(df["surface_reelle_bati"].to_numpy(dtype=float))
    x_rooms = df["nombre_pieces_principales"].to_numpy(dtype=float)

    X = np.column_stack([np.ones(len(df)), x_surface, x_rooms])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)

    residuals = y - (X @ beta)
    sigma = _mad_sigma(residuals)
    if not math.isfinite(sigma) or sigma <= 0:
        sigma = float(np.std(residuals, ddof=1))

    model = PriceModel(
        b0=float(beta[0]),
        b_log_surface=float(beta[1]),
        b_rooms=float(beta[2]),
        sigma=float(sigma),
        n_train=int(len(df)),
        type_local="Appartement",
    )

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(model), indent=2), encoding="utf-8")
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", default="artifacts/model.json")
    args = parser.parse_args()

    model = train_model(args.csv, args.out)
    print(f"Saved {args.out}: n_train={model.n_train}, sigma={model.sigma:.4f}, type_local={model.type_local}")


if __name__ == "__main__":
    main()