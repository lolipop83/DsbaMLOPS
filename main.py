# main.py
from fastapi import FastAPI
from ui import router as ui_router
from validation import validate_inputs
from score import score_price

app = FastAPI()
app.include_router(ui_router)


@app.get("/score")
def get_score(surface: int, nb_room: int, price: float) -> dict:
    validate_inputs(surface=surface, nb_room=nb_room, price=price)
    return score_price(surface=surface, nb_room=nb_room, price=price)
#http://127.0.0.1:8000/docs