# main.py
from fastapi import FastAPI, Query, HTTPException
from ui import router as ui_router
from validation import validate_inputs
from score import score_price
from model_loader import load_model
from project_config import load_project_config, list_projects, get_active_project_name

# chargement de tous les projets au démarrage
_default_project = get_active_project_name()
_projects: dict[str, dict] = {}

for _name in list_projects():
    _cfg = load_project_config(_name)
    _mdl = load_model(_name)
    _lab = _cfg.get("labeling", {})
    _projects[_name] = {
        "config": _cfg,
        "model": _mdl,
        "validation": _cfg.get("validation"),
        "threshold_low": float(_lab.get("underpriced_below", 0.9)),
        "threshold_high": float(_lab.get("overpriced_above", 1.1)),
    }


def _resolve(project: str | None) -> dict:
    name = project or _default_project
    if name not in _projects:
        raise HTTPException(status_code=404, detail=f"Projet inconnu : '{name}'. Disponibles : {list(_projects.keys())}")
    return _projects[name]


app = FastAPI(
    title="Mini-plateforme MLOps — Estimation de prix immobilier",
)
app.include_router(ui_router)


@app.get("/projects")
def get_projects() -> dict:
    """Liste des projets disponibles."""
    return {
        "active": _default_project,
        "available": [
            {"name": name, "project_name": p["config"].get("project_name", name)}
            for name, p in _projects.items()
        ],
    }


@app.get("/score")
def get_score(
    surface: float = Query(..., gt=0),
    nb_room: int = Query(..., gt=0),
    price: float = Query(..., gt=0),
    project: str | None = Query(None, description="Nom du projet (si omis, projet actif)"),
) -> dict:
    p = _resolve(project)
    validate_inputs(surface=surface, nb_room=nb_room, price=price, validation_cfg=p["validation"])
    return score_price(
        model=p["model"],
        surface=surface,
        nb_room=nb_room,
        price=price,
        threshold_low=p["threshold_low"],
        threshold_high=p["threshold_high"],
    )


@app.get("/info")
def get_info(project: str | None = Query(None, description="Nom du projet (si omis, projet actif)")) -> dict:
    """Informations sur un projet et son modèle."""
    p = _resolve(project)
    cfg = p["config"]
    mdl = p["model"]
    return {
        "project_name": cfg.get("project_name"),
        "location": cfg.get("location"),
        "data": cfg.get("data"),
        "model_version": mdl.version,
        "model_n_train": mdl.n_train,
        "model_sigma": round(mdl.sigma, 4),
        "model_type_local": mdl.type_local,
    }
# http://127.0.0.1:8000/docs
