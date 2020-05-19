from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.datastructures import URLPath
from starlette.requests import Request

from minihai.app.utils import make_list_response
from minihai.models.execution import Execution
from minihai.models.output import get_output_cache, Output

router = APIRouter()


@router.get("/api/v0/data/")
def list_data(output_execution: str = None):
    if not output_execution:
        return JSONResponse(
            {"error": "This API requires the output_execution parameter"}, 400
        )
    execution = Execution.load(id=output_execution)
    output_datas = []

    output_cache = get_output_cache()
    for output in execution.iterate_outputs():
        output.cache(output_cache)
        output_datas.append(output.as_api_response())
    return make_list_response(output_datas)


@router.get("/api/v0/data/{id}/download/")
def get_datum_download_url(request: Request, id: str = Path()):
    output = Output.from_cache(id)
    if not output:
        return JSONResponse({"error": "Output not found in cache"}, 404)
    url = URLPath(output.download_url).make_absolute_url(base_url=request.base_url)
    return {
        "url": url,
    }
