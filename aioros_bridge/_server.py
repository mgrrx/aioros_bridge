from starlette.applications import Starlette
from starlette.routing import Mount, WebSocketRoute, request_response

from ._api import routes as api_routes
from ._lifespan import lifespan
from ._websocket import ROSBridgeEndpoint

routes = [
    WebSocketRoute("/ws", ROSBridgeEndpoint),
    Mount("/api", routes=api_routes),
]

try:
    import sse_starlette  # pylint: disable=unused-import
except ImportError:
    pass
else:
    from ._sse import sse
    routes.append(Mount("/topic", request_response(sse)))

app = Starlette(
    debug=True,
    routes=routes,
    lifespan=lifespan,
)
