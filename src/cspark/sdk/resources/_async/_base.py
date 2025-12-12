import asyncio
from typing import Any, Mapping, Optional, Union

from httpx import URL, AsyncClient, HTTPError, HTTPStatusError, Request, RequestError

from ..._config import Config
from ..._errors import SparkApiError, SparkError
from ..._logger import get_logger
from ..._utils import get_retry_timeout, get_uuid
from ..._version import about, sdk_ua_header
from .._base import HttpResponse, Uri

__all__ = ['AsyncApiResource']


class AsyncApiResource:
    def __init__(self, config: Config, http_client: AsyncClient):
        self.config = config
        self.logger = get_logger(**config.logger.__dict__)
        self._client = http_client

    @property
    def default_headers(self):
        return {
            **self.config.extra_headers,
            'User-Agent': about,
            'x-spark-ua': sdk_ua_header,
            'x-request-id': get_uuid(),
            'x-tenant-name': self.config.base_url.tenant,
        }

    async def request(
        self,
        url: Union[str, 'Uri', URL],
        *,
        method: str = 'GET',
        headers: Mapping[str, str] = {},
        params: Optional[Mapping[str, str]] = None,
        body: Optional[Any] = None,
        content: Optional[bytes] = None,
        form: Optional[Any] = None,
        files: Optional[Any] = None,
    ) -> 'HttpResponse':
        url = str(url)
        request = self._client.build_request(
            method,
            url,
            params=params,
            headers={**headers, **self.default_headers},
            data=form,
            json=body,
            content=content,
            files=files,
        )

        self.logger.debug(f'{method} {url}')
        return await self.__fetch(request)

    async def __fetch(self, request: Request, retries: int = 0) -> HttpResponse:
        request.headers.update(self.config.auth.as_header)

        response, status_code = None, 0
        err_msg = f'an error occurred while fetching <{request.url}>'

        try:
            response = await self._client.send(request)
            response.raise_for_status()
        except RequestError as err:
            err_msg += f'; {err}'  # occurs while issuing a request; hence no response
            raise SparkError.sdk(err_msg, SparkApiError.no_response(request)) from err
        except HTTPStatusError as err:
            err_msg = str(err)
        except HTTPError as err:
            err_msg += f'; {err}'
        except Exception:
            pass  # possibly runtime error but should not interrupt this flow

        if not response:
            raise SparkError.sdk(err_msg, SparkApiError.no_response(request))

        status_code = response.status_code
        if status_code >= 400:
            if status_code == 401 and self.config.auth.type == 'oauth' and retries < self.config.max_retries:
                await self.config.auth.oauth.aretrieve_token(self.config, self._client)  # type: ignore
                return await self.__fetch(request, retries + 1)

            if (status_code == 408 or status_code == 429) and retries < self.config.max_retries:
                self.logger.debug(f'retrying request due to status code {status_code}...')
                delay = get_retry_timeout(retries, self.config.retry_interval)
                await asyncio.sleep(delay)
                return await self.__fetch(request, retries + 1)

            raise SparkError.api(
                status_code,
                {'message': f'failed to fetch <{request.url}>', 'cause': SparkApiError.to_cause(request, response)},
            )

        # otherwise, ok response
        ok_response = {
            'status': status_code,
            'data': None,
            'buffer': response.content,
            'headers': response.headers,
            'raw_request': request,
            'raw_response': response,
        }

        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            try:
                ok_response['data'] = response.json()
            except Exception:
                ok_response['data'] = response.text
        return HttpResponse(**ok_response)
