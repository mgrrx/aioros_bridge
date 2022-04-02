from typing import List, Tuple, cast

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route, request_response

from aioros.abc import Node


def filter_for_node(registry: List[Tuple[str, List[str]]], node: str) -> List[str]:
    return [key for key, nodes in registry if node in nodes]


async def nodes(request: Request) -> JSONResponse:
    system_state = await request.app.node._master.get_system_state()

    path = request["path"]
    if path == "/":
        result = set()
        for state in system_state:
            for _, node_names in state:
                result |= set(node_names)
        return JSONResponse(sorted(result))

    data = {
        "publishing": filter_for_node(system_state[0], path),
        "subscribing": filter_for_node(system_state[1], path),
        "services": filter_for_node(system_state[2], path),
    }
    if not any(data.values()):
        return JSONResponse({"detail": f"Node {path} does not exist."}, 400)
    return JSONResponse(data)


async def topics(request: Request) -> JSONResponse:
    topic_types = dict(await request.app.node._master.get_topic_types())

    path = request["path"]
    if path == "/":
        return JSONResponse(
            [
                {"topic": topic, "type": topic_types[topic]}
                for topic in sorted(topic_types.keys())
            ]
        )

    system_state = await request.app.node._master.get_system_state()
    publications = dict(system_state[0])
    subscriptions = dict(system_state[1])

    if path not in topic_types:
        return JSONResponse({"detail": f"Topic {path} does not exist."}, 400)
    return JSONResponse(
        {
            "type": topic_types[path],
            "publishing": publications.get(path, []),
            "subscribing": subscriptions.get(path, []),
        }
    )


async def parameters(request: Request) -> JSONResponse:
    node = cast(Node, request.app.node)
    path = request["path"]
    try:
        if request.method == "GET":
            if path == "/":
                return JSONResponse(sorted(await node.get_param_names()))
            return JSONResponse(await node.get_param(path))
        if request.method == "DELETE":
            await node.delete_param(path)
            return JSONResponse({})
        if request.method == "PUT":
            await node.set_param(path, await request.json())
            return JSONResponse({})
    except KeyError as exc:
        return JSONResponse({"detail": str(exc)}, 400)
    return JSONResponse({"detail": "Invalid method"}, 400)


class Services(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        system_state = await request.app.node._master.get_system_state()
        return JSONResponse(sorted(service_name for service_name, _ in system_state[2]))


class Time(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        time = cast(Node, request.app.node).get_time()
        return JSONResponse(
            {
                "secs": time.secs,
                "nsecs": time.nsecs,
            }
        )


routes = [
    Mount("/nodes", request_response(nodes)),
    Mount("/topics", request_response(topics)),
    Mount("/params", request_response(parameters)),
    Route("/services", Services),
    Route("/time", Time),
]
