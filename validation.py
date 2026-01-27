from fastapi import HTTPException


def validate_inputs(address_id: int, surface: int, nb_room: int):
    if address_id <= 0:
        raise HTTPException(status_code=422, detail="address_id must be > 0")
    if surface <= 0:
        raise HTTPException(status_code=422, detail="surface must be > 0")
    if nb_room <= 0:
        raise HTTPException(status_code=422, detail="nb_room must be > 0")
