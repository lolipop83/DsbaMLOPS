from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello Word" }


def myAPI(address_id : int, surface: int, nb_room: int):
    if address_id.is_integer :
        if surface.is_integer:
            if nb_room.is_integer:
                return myScore(address_id, surface,nb_room)
            
    
    