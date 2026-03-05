# ui.py
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/", include_in_schema=False)
def ui() -> FileResponse:
    return FileResponse("static/index.html")