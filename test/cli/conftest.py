from __future__ import annotations

from datetime import datetime
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from cspark.cli._main import main
from cspark.cli._utils import Profile


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def cli():
    return main


@pytest.fixture
def active_profile() -> Profile:
    now = datetime.now().isoformat()
    return Profile(
        name='test',
        is_active=True,
        created_at=now,
        updated_at=now,
        base_url='https://excel.test.coherent.global/tenant',
        api_key='test-api-key',
        timeout=60000,
        max_retries=2,
        retry_interval=0.01,
        logger=False,
    )


def make_response(data=None, status: int = 200, buffer: bytes = b'') -> MagicMock:
    response = MagicMock()
    response.data = data if data is not None else {}
    response.status = status
    response.buffer = buffer
    return response


_PROFILE_PATCH_TARGETS = (
    'cspark.cli._commands._health.get_active_profile',
    'cspark.cli._commands._folders.get_active_profile',
    'cspark.cli._commands._services.get_active_profile',
    'cspark.cli._commands._transforms.get_active_profile',
    'cspark.cli._commands._logs.get_active_profile',
    'cspark.cli._commands._impex.get_active_profile',
    'cspark.cli._commands._wasm.get_active_profile',
    'cspark.cli._commands._files.get_active_profile',
)

_CLIENT_PATCH_TARGETS = (
    'cspark.cli._commands._health.Client',
    'cspark.cli._commands._folders.Client',
    'cspark.cli._commands._services.Client',
    'cspark.cli._commands._transforms.Client',
    'cspark.cli._commands._logs.Client',
    'cspark.cli._commands._impex.Client',
    'cspark.cli._commands._wasm.Client',
    'cspark.cli._commands._files.Client',
)


@pytest.fixture
def mock_client(active_profile: Profile) -> Iterator[MagicMock]:
    client = MagicMock()
    client.config.max_retries = 2
    client.config.retry_interval = 0.01
    client.config.extra_headers = {}
    client.config.base_url.value = 'https://excel.test.coherent.global/tenant'
    client.__enter__.return_value = client
    client.__exit__.return_value = False

    patches = [patch(target, return_value=active_profile) for target in _PROFILE_PATCH_TARGETS]
    patches.extend(patch(target, return_value=client) for target in _CLIENT_PATCH_TARGETS)

    for p in patches:
        p.start()
    try:
        yield client
    finally:
        for p in patches:
            p.stop()
