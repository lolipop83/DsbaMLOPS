from fastapi import FastAPI, HTTPException
from score import myScore

app = FastAPI()


@app.get("/score/{address_id}")
def GetScore(address_id: int, surface: int, nb_room: int):
    if surface <= 0:
        raise HTTPException(status_code=422, detail="surface must be > 0")

    result = myScore(address_id, surface, nb_room)
    return {"Score": result}

#http://127.0.0.1:8000/docs
#http://127.0.0.1:8000/score/4?surface=5&nb_room=6
