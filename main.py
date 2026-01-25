from fastapi import FastAPI
from validation import validate_inputs
from score import get_score

app = FastAPI()

@app.get("/score/{address_id}")

def house_scoring(address_id: int,  surface: int, nb_room: int):
    validate_inputs(address_id=address_id, surface=surface, nb_room=nb_room)  
    result = get_score(address_id=address_id, surface=surface, nb_room=nb_room)  
    return {"score": result}   
 
#http://127.0.0.1:8000/docs
#http://127.0.0.1:8000/score/4?surface=5&nb_room=6