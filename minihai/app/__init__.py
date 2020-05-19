from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from .routers import misc, commits, executions, data
from .. import conf

app = FastAPI()
app.include_router(misc.router)
app.include_router(commits.router)
app.include_router(executions.router)
app.include_router(data.router)
app.mount("/data", StaticFiles(directory=conf.settings.data_path), name="data")
