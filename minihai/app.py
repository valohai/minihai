from fastapi import FastAPI

import minihai

app = FastAPI()


@app.get("/")
def read_root():
    return {"version": minihai.__version__}
