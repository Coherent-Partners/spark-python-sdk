import json
from typing import Any, Callable, Optional, Union

import click
from cspark.sdk import ApiResource, Uri


def header_option(**kwargs: Any) -> Callable:
    """Define a decorator that applies click.option with dynamic parameters"""

    def decorator(func: Union[Callable, click.Command]) -> Union[Callable, click.Command]:
        return click.option(
            '-H',
            '--header',
            type=str,
            multiple=True,  # allows multiple headers to be provided
            help='Headers to send with the request (e.g., "x-my-header: value")',
            metavar='<HEADER>',
            **kwargs,
        )(func)

    return decorator


def parse_headers(headers: list[str]) -> dict[str, str]:
    parsed_headers = {}
    for header in headers:
        key, value = header.split(':', 1)
        parsed_headers[key.strip()] = value.strip()
    return parsed_headers


class Services(ApiResource):
    def get(self, folder: str, data: Optional[str] = None):
        endpoint = f'product/{folder}/engines'
        url = Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)
        body = {'page': 1, 'pageSize': 100, 'search': [], 'sort': 'name1'}
        return self.request(url, method='POST', body=body.update(json.loads(data)) if data else body)
