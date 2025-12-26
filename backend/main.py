
from fastapi import FastAPI
from routes import router

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to MiniMaxing Backend!"}

app.include_router(router)
