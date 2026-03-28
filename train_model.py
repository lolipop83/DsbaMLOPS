# train_model.py
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


@dataclass(frozen=True)
class PriceModel:
    b0: float
    b_log_surface: float
    b_rooms: float
    sigma: float
    n_train: int
    type_local: str
    version: str = ""


def _mad_sigma(residuals: np.ndarray) -> float:
    med = np.median(residuals)
    mad = np.median(np.abs(residuals - med))
    return float(1.4826 * mad)


def _r_squared(y: np.ndarray, y_hat: np.ndarray) -> float:
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def train_model(csv_path: str, out_dir: str, *, type_local: str = "Appartement", csv_sep: str = ";") -> PriceModel:
    df = pd.read_csv(csv_path, sep=csv_sep)

    df["type_local"] = df["type_local"].astype(str)
    df = df[df["type_local"] == type_local]

    for col in ["valeur_fonciere", "surface_reelle_bati", "nombre_pieces_principales"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati", "nombre_pieces_principales"])
    df = df[(df["valeur_fonciere"] > 1000) & (df["surface_reelle_bati"] > 5)]
    df = df[df["nombre_pieces_principales"] > 0]

    if len(df) < 30:
        raise ValueError(f"Not enough rows after filtering to {type_local} only: n={len(df)}")

    y = np.log(df["valeur_fonciere"].to_numpy(dtype=float))
    x_surface = np.log(df["surface_reelle_bati"].to_numpy(dtype=float))
    x_rooms = df["nombre_pieces_principales"].to_numpy(dtype=float)

    X = np.column_stack([np.ones(len(df)), x_surface, x_rooms])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)

    residuals = y - (X @ beta)
    sigma = _mad_sigma(residuals)
    if not math.isfinite(sigma) or sigma <= 0:
        sigma = float(np.std(residuals, ddof=1))

    r2 = _r_squared(y, X @ beta)
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    model = PriceModel(
        b0=float(beta[0]),
        b_log_surface=float(beta[1]),
        b_rooms=float(beta[2]),
        sigma=float(sigma),
        n_train=int(len(df)),
        type_local=type_local,
        version=version,
    )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    model_dict = asdict(model)

    # modèle actif (écrasé)
    (out / "model.json").write_text(json.dumps(model_dict, indent=2), encoding="utf-8")
    # copie versionnée (archivage)
    (out / f"model_{version}.json").write_text(json.dumps(model_dict, indent=2), encoding="utf-8")

    # journal de métriques (append)
    log_entry = {
        "version": version,
        "n_train": model.n_train,
        "sigma": round(model.sigma, 6),
        "r_squared": round(r2, 4),
        "b0": round(model.b0, 6),
        "b_log_surface": round(model.b_log_surface, 6),
        "b_rooms": round(model.b_rooms, 6),
        "csv_path": csv_path,
    }
    with open(out / "model_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"Saved {out}/model.json: n_train={model.n_train}, sigma={model.sigma:.4f}, r2={r2:.4f}, version={version}")
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=None, help="Chemin CSV DVF (si omis, cherché dans le dossier du projet)")
    parser.add_argument("--project", default=None, help="Nom du projet (dossier sous projects/)")
    args = parser.parse_args()

    # résoudre le dossier projet
    base = Path(__file__).resolve().parent
    if args.project:
        project_dir = base / "projects" / args.project
    else:
        cfg = yaml.safe_load((base / "config.yaml").read_text(encoding="utf-8"))
        project_dir = base / "projects" / cfg["active_project"]

    # lire la config projet
    project_cfg_path = project_dir / "config.yaml"
    type_local = "Appartement"
    csv_sep = ";"
    csv_filename = None
    if project_cfg_path.exists():
        pcfg = yaml.safe_load(project_cfg_path.read_text(encoding="utf-8"))
        type_local = pcfg.get("data", {}).get("type_local", type_local)
        csv_sep = pcfg.get("data", {}).get("csv_separator", csv_sep)
        csv_filename = pcfg.get("data", {}).get("csv_filename")

    # résoudre le CSV
    if args.csv:
        csv_path = args.csv
    elif csv_filename:
        csv_path = str(project_dir / csv_filename)
    else:
        raise FileNotFoundError(f"Aucun CSV spécifié (ni --csv, ni csv_filename dans {project_cfg_path})")

    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV introuvable : {csv_path}")

    train_model(csv_path, str(project_dir), type_local=type_local, csv_sep=csv_sep)


if __name__ == "__main__":
    main()
