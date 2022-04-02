from contextlib import asynccontextmanager
from itertools import count
from typing import AsyncIterator

import anyio
import pytest
from genpy import Duration
from starlette.applications import Starlette
from std_msgs.msg import String

from aioros import init_node
from aioros.abc import Node
from aioros.master import init_master
from aioros_bridge._server import routes


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with init_master() as master, init_node(
        "test_publisher",
        master_uri=master.xmlrpc_uri,
        register_signal_handler=False,
        configure_logging=False,
    ) as publisher_node, init_node(
        "aioros_web",
        master_uri=master.xmlrpc_uri,
        register_signal_handler=False,
        configure_logging=False,
    ) as app.node, anyio.create_task_group() as task_group:
        task_group.start_soon(publish_content, publisher_node)
        yield
        task_group.cancel_scope.cancel()


async def publish_content(node: Node) -> None:
    async with node.create_publication("/chatter", String) as publisher:
        counter = count()
        while node.is_running():
            msg = String(f"Message {next(counter)}")
            await publisher.publish(msg)
            await node.sleep(Duration(1.0))


@pytest.fixture(name="app_with_publisher")
def fixture_app_with_publisher() -> Starlette:
    return Starlette(
        routes=routes,
        lifespan=lifespan,
    )
