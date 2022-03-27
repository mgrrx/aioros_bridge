from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.routing import Route

from .._node._node import init_node
from ._sse import sse


@asynccontextmanager
async def lifespan(app: Starlette):
    async with init_node(
        "aioros_web",
        register_signal_handler=False,
        debug=True,
    ) as node:
        app.state.node = node
        yield
        app.state.node = None


routes = [
    Route("/{topic_name}", endpoint=sse),
]

app = Starlette(debug=True, routes=routes, lifespan=lifespan)
