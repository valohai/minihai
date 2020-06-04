import datetime
from typing import Union


def format_log_event(
    *, stream: str, message: str, time: Union[str, datetime.datetime] = None
) -> dict:
    if not time:
        time = datetime.datetime.now()
    if not isinstance(time, str):
        time = time.isoformat()
    return {
        "stream": stream,
        "message": str(message),
        "time": time,
    }
