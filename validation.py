from fastapi import HTTPException


def validate_inputs(surface: int, nb_room: int, price: float) -> None:
    if surface <= 0:
        raise HTTPException(status_code=422, detail="surface must be > 0")
    if nb_room <= 0:
        raise HTTPException(status_code=422, detail="nb_room must be > 0")
    if price <= 0:
        raise HTTPException(status_code=422, detail="price must be > 0")