import typing

import pytest
from uvicorn.config import Config

from .resources._server import LocalServer, router, serve_in_thread


@pytest.fixture(scope='session')
def server() -> typing.Iterator[LocalServer]:
    config = Config(app=router, lifespan='off', loop='asyncio')
    server = LocalServer(config=config)
    yield from serve_in_thread(server)
