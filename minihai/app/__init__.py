from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from .auth import MinihaiAuth
from .routers import misc, commits, executions, data, public
from .. import conf

app = FastAPI()
app.include_router(public.router)
app.include_router(misc.router, dependencies=[MinihaiAuth])
app.include_router(commits.router, dependencies=[MinihaiAuth])
app.include_router(executions.router, dependencies=[MinihaiAuth])
app.include_router(data.router, dependencies=[MinihaiAuth])
# TODO: add auth to static files
app.mount("/data", StaticFiles(directory=conf.settings.data_path), name="data")
