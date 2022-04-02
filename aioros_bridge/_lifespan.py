from contextlib import asynccontextmanager
from typing import AsyncIterator

from starlette.applications import Starlette

from aioros import init_node


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with init_node(
        "aioros_web",
        register_signal_handler=False,
        debug=app.debug,
    ) as app.node:
        yield
