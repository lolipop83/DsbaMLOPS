from fastapi import HTTPException


_DEFAULTS = {
    "surface_min": 9,
    "surface_max": 300,
    "nb_room_min": 1,
    "nb_room_max": 10,
    "price_min": 20_000,
    "price_max": 3_000_000,
    "price_per_sqm_min": 500,
    "price_per_sqm_max": 15_000,
}


def _get(cfg: dict | None, key: str) -> float:
    if cfg and key in cfg:
        return float(cfg[key])
    return float(_DEFAULTS[key])


def validate_inputs(surface: float, nb_room: int, price: float, validation_cfg: dict | None = None) -> None:
    # élémentaire
    if surface <= 0:
        raise HTTPException(status_code=422, detail="surface must be > 0")
    if nb_room <= 0:
        raise HTTPException(status_code=422, detail="nb_room must be > 0")
    if price <= 0:
        raise HTTPException(status_code=422, detail="price must be > 0")

    # bornes métier
    s_min, s_max = _get(validation_cfg, "surface_min"), _get(validation_cfg, "surface_max")
    if not (s_min <= surface <= s_max):
        raise HTTPException(status_code=422, detail=f"surface hors bornes réalistes ({s_min}–{s_max} m²)")

    r_min, r_max = int(_get(validation_cfg, "nb_room_min")), int(_get(validation_cfg, "nb_room_max"))
    if not (r_min <= nb_room <= r_max):
        raise HTTPException(status_code=422, detail=f"nb_room hors bornes réalistes ({r_min}–{r_max})")

    p_min, p_max = _get(validation_cfg, "price_min"), _get(validation_cfg, "price_max")
    if not (p_min <= price <= p_max):
        raise HTTPException(status_code=422, detail=f"price hors bornes réalistes ({p_min:,.0f}–{p_max:,.0f} €)")

    # cohérence croisée €/m²
    price_sqm = price / surface
    sqm_min, sqm_max = _get(validation_cfg, "price_per_sqm_min"), _get(validation_cfg, "price_per_sqm_max")
    if not (sqm_min <= price_sqm <= sqm_max):
        raise HTTPException(
            status_code=422,
            detail=f"Prix/m² calculé ({price_sqm:,.0f} €/m²) hors bornes plausibles ({sqm_min:,.0f}–{sqm_max:,.0f} €/m²). Vérifiez la surface et le prix.",
        )
