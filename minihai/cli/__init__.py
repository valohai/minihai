import click
import uvicorn

import minihai
from minihai.art import BANNER


@click.group()
def main():
    pass


@main.command(help="Start the Minihai server.")
@click.option("-h", "--host", default="127.0.0.1")
@click.option("-p", "--port", default=8000, type=int)
@click.option("--debug/--no-debug", default=False)
def start(host, port, debug=False):
    print(f"{BANNER} :: {minihai.__version__}")
    uvicorn.run(
        "minihai.app:app", host=host, port=port, debug=debug, reload=debug,
    )
