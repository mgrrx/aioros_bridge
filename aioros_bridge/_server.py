from starlette.applications import Starlette
from starlette.routing import Route

from ._lifespan import lifespan
from ._sse import sse

routes = [
    Route("/{topic_name}", endpoint=sse),
]

app = Starlette(
    debug=True,
    routes=routes,
    lifespan=lifespan,
)
