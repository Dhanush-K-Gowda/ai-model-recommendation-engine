from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    price: float
    description: str | None = None


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}


@app.post("/items/")
async def create_item(item: Item):
    return {"item": item}

