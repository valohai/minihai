from fastapi import FastAPI

from .routers import misc, commits, executions

app = FastAPI()
app.include_router(misc.router)
app.include_router(commits.router)
app.include_router(executions.router)
