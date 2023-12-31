from fastapi import APIRouter


router = APIRouter()


@router.get("/index")
def index():
    return "Hello World"
