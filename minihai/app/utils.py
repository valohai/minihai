from typing import List


def make_list_response(results: List[dict]):
    return {
        "count": len(results),
        "next": None,
        "previous": None,
        "results": results,
    }
