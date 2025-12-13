from json import dumps
from math import ceil
from typing import Any, Dict, List, Optional, Union, cast

from httpx import AsyncClient

from ..._config import Config
from ..._constants import SPARK_SDK
from ..._errors import SparkError
from ..._utils import StringUtils, get_uuid, is_not_empty_list
from .._base import Uri, UriParams
from .._batches import BatchChunk, ChunkData
from ._base import AsyncApiResource

__all__ = ['AsyncBatches', 'AsyncPipeline']


class AsyncBatches(AsyncApiResource):
    @property
    def base_uri(self) -> dict[str, str]:
        return {'base_url': self.config.base_url.full, 'version': 'api/v4'}

    async def describe(self):
        """Describes the batch pipeline status across the tenant."""
        url = Uri.of(None, endpoint=f'batch/status', **self.base_uri)
        return await self.request(url, method='GET')

    async def create(
        self,
        uri: Union[str, UriParams],
        *,
        # Metadata for calculations
        active_since: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        call_purpose: Optional[str] = None,
        subservices: Union[None, str, List[str]] = None,
        selected_outputs: Union[None, str, List[str]] = None,
        unique_record_key: Union[None, str, List[str]] = None,
        # Experimental parameters (likely to change/be deprecated in future releases)
        min_runners: Optional[int] = None,
        max_runners: Optional[int] = None,
        chunks_per_vm: Optional[int] = None,
        runners_per_vm: Optional[int] = None,
        max_input_size: Optional[float] = None,
        max_output_size: Optional[float] = None,
        accuracy: Optional[float] = None,
    ):
        uri = Uri.validate(uri)
        url = Uri.of(base_url=self.config.base_url.full, version='api/v4', endpoint='batch')
        service_uri = uri.pick('folder', 'service', 'version').encode(long=False)
        body = {
            'service': uri.service_id or service_uri or None,
            'version_id': uri.version_id,
            'version_by_timestamp': active_since,
            'subservice': StringUtils.join(subservices),
            'output': StringUtils.join(selected_outputs),
            'call_purpose': call_purpose or 'Async Batch Execution',
            'source_system': source_system or SPARK_SDK,
            'correlation_id': correlation_id,
            'unique_record_key': StringUtils.join(unique_record_key),
            # experimental pipeline options
            'initial_workers': min_runners,
            'max_workers': max_runners,
            'chunks_per_request': chunks_per_vm,
            'runner_thread_count': runners_per_vm,
            'max_input_size': max_input_size,
            'max_output_size': max_output_size,
            'acceptable_error_percentage': ceil((1 - min(accuracy or 1, 1.0)) * 100),
        }

        return await self.request(url, method='POST', body={k: v for k, v in body.items() if v is not None})

    def of(self, batch_id: str) -> 'AsyncPipeline':
        return AsyncPipeline(batch_id, self.config, self._client)


class AsyncPipeline(AsyncApiResource):
    _state: str = 'open'
    _chunks: Dict[str, int] = dict()

    def __init__(self, batch_id: str, config: Config, http_client: AsyncClient):
        super().__init__(config, http_client)
        self._id = batch_id

        if StringUtils.is_empty(batch_id):
            error = SparkError.sdk('batch pipeline id is required to proceed', batch_id)
            self.logger.error(error.message)
            raise error

    @property
    def base_uri(self) -> dict[str, str]:
        return {'base_url': self.config.base_url.full, 'version': 'api/v4'}

    @property
    def batch_id(self) -> str:
        return self._id

    @property
    def state(self) -> str:
        return self._state

    @property
    def stats(self) -> Dict[str, int]:
        return {'chunks': len(self._chunks), 'records': sum(self._chunks.values())}

    @property
    def is_disposed(self) -> bool:
        """
        Determines if the batch pipeline is no longer active.

        This is for the internal use of the SDK and does not validate the actual state
        of the batch pipeline. Use `getStatus()` to get the actual state of the batch
        pipeline.
        """
        return self._state == 'closed' or self._state == 'cancelled'

    async def get_info(self):
        """Retrieves the batch pipeline info."""
        url = Uri.of(None, endpoint=f'batch/{self._id}', **self.base_uri)
        return await self.request(url, method='GET')

    async def get_status(self):
        """Retrieves the batch pipeline status."""
        url = Uri.of(None, endpoint=f'batch/{self._id}/status', **self.base_uri)
        return await self.request(url, method='GET')

    async def push(
        self,
        *,
        chunks: Optional[List[BatchChunk]] = None,
        data: Optional[ChunkData] = None,
        inputs: Optional[List[Any]] = None,
        raw: Union[None, str, bytes] = None,
        if_chunk_id_duplicated: str = 'replace',  # 'ignore' | 'replace' | 'throw'
    ):
        self.__assert_state(['closed', 'cancelled'])

        url = Uri.of(None, endpoint=f'batch/{self._id}/chunks', **self.base_uri)
        body = self.__build_chunk_data(chunks, data, inputs, raw, if_chunk_id_duplicated)

        response = await self.request(url, method='POST', body=body)
        total = response.data['record_submitted'] if isinstance(response.data, dict) else 0
        self.logger.info(f'pushed {total} records to batch pipeline <{self._id}>')

        return response

    async def pull(self, max_chunks: int = 100):
        self.__assert_state(['cancelled'])

        endpoint = f'batch/{self._id}/chunkresults?max={max(1, max_chunks)}'

        response = await self.request(Uri.of(None, endpoint=endpoint, **self.base_uri))
        total = response.data['status']['records_available'] if isinstance(response.data, dict) else 0
        self.logger.info(f'{total} available records from batch pipeline <{self._id}>')

        return response

    async def dispose(self, state: str = 'closed'):
        """Disposes the batch pipeline."""
        self.__assert_state(['closed', 'cancelled'])

        url = Uri.of(None, endpoint=f'batch/{self._id}', **self.base_uri)

        response = await self.request(url, method='PATCH', body={'batch_status': state})
        self.logger.info(f'batch pipeline <{self._id}> has been {state}')
        self._state = state

        return response

    async def cancel(self):
        return await self.dispose(state='cancelled')

    def __assert_state(self, states: List[str], throwable: bool = True) -> bool:
        if self._state in states:
            error = SparkError.sdk(f'batch pipeline <{self._id}> is already {self._state}')
            self.logger.error(error.message)
            if throwable:
                raise error
            return False
        return True

    def __build_chunk_data(
        self,
        chunks: Optional[List[BatchChunk]] = None,
        data: Optional[ChunkData] = None,
        inputs: Optional[List[Any]] = None,
        raw: Union[None, str, bytes] = None,
        if_duplicated: str = 'replace',
    ):
        try:
            if raw is not None and StringUtils.is_not_empty(raw):
                chunks = BatchChunk.from_str(raw)  # takes precedence over other entries

            if is_not_empty_list(chunks):
                return {'chunks': self.__assess_chunks(cast(List[BatchChunk], chunks), if_duplicated)}
            if isinstance(data, ChunkData) and is_not_empty_list(data.inputs):
                return {'chunks': self.__assess_chunks([BatchChunk(id=get_uuid(), data=data)], if_duplicated)}
            if is_not_empty_list(inputs):
                data = ChunkData(inputs=cast(List[Any], inputs), parameters={})
                return {'chunks': self.__assess_chunks([BatchChunk(id=get_uuid(), data=data)], if_duplicated)}

            cause = {'chunks': chunks, 'data': data, 'inputs': inputs, 'raw': raw}
            raise SparkError.sdk(
                message=f'wrong data params were provided for this pipeline <{self._id}>.\n'
                'Expecting either "raw=str/bytes", "chunks=List[BatchChunk]", "data=ChunkData" or "inputs=List[Any]"',
                cause=dumps(cause),
            )
        except SparkError as error:
            self.logger.error(error.message)
            raise
        except Exception as cause:
            raise SparkError.sdk('failed to build push data for batch pipeline', cause) from cause

    def __assess_chunks(self, chunks: List['BatchChunk'], is_duplicated: str):
        assessed = []
        for chunk in chunks:
            id = get_uuid() if StringUtils.is_empty(chunk.id) else chunk.id
            if chunk.id in self._chunks:
                if is_duplicated == 'ignore':
                    self.logger.warning(
                        f'chunk id <{id}> appears to be duplicated for this pipeline <{self._id}> '
                        f'and may cause unexpected behavior. You should consider using a different id.'
                    )
                    continue
                if is_duplicated == 'throw':
                    raise SparkError.sdk(
                        message=f'chunk id <{id}> is duplicated for batch pipeline <{self._id}>',
                        cause=chunk,
                    )
                if is_duplicated == 'replace':
                    self._chunks.pop(chunk.id)  # remove the old chunk id
                    chunk.id = get_uuid()  # add new id for the chunk
                    self.logger.info(
                        f'chunk id <{id}> is duplicated for this pipeline <{self._id}> '
                        f'and has been replaced with <{chunk.id}>'
                    )
            self._chunks[chunk.id] = chunk.size or len(chunk.data.inputs) - 1
            assessed.append(chunk.to_dict())
        return assessed
