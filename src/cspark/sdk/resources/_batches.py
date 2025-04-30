import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, cast

from .._config import Config
from .._constants import SPARK_SDK
from .._errors import SparkError
from .._utils import StringUtils, get_uuid, is_not_empty_list
from ._base import ApiResource, Uri, UriParams

__all__ = ['Batches', 'Pipeline', 'BatchChunk', 'ChunkData', 'create_chunks']


@dataclass
class ChunkData:
    inputs: List[Any]
    parameters: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ChunkData':
        """Creates a chunk data object from dictionary-based data."""
        return ChunkData(data.get('inputs', []), data.get('parameters', {}), data.get('summary'))

    @staticmethod
    def from_str(data: Union[str, bytes]) -> 'ChunkData':
        """Creates a chunk data object from string-based data."""
        try:
            return ChunkData.from_dict(json.loads(data))
        except json.JSONDecodeError as err:
            raise SparkError.sdk('failed to parse string/bytes data as JSON', cause=err) from err
        except Exception as exc:
            raise SparkError.sdk(f'cannot create chunk data from {data}', cause=exc) from exc


@dataclass
class BatchChunk:
    id: str
    data: ChunkData
    size: Optional[int] = None

    def to_dict(self):
        return {'id': self.id, 'data': self.data.to_dict(), 'size': self.size or len(self.data.inputs)}

    @staticmethod
    def from_dict(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List['BatchChunk']:
        """Creates a list of batch chunks from dictionary-based data."""
        if isinstance(data, dict):
            data = [data]

        chunks = []
        for chunk in data:
            if not isinstance(chunk, dict):
                continue

            id = chunk.get('id', get_uuid())
            chunk_data = ChunkData.from_dict(chunk.get('data', {}))
            size = chunk.get('size', len(chunk_data.inputs))

            chunks.append(BatchChunk(id, data=chunk_data, size=size))
        return chunks

    @staticmethod
    def from_str(data: Union[str, bytes]) -> List['BatchChunk']:
        """Creates a list of batch chunks from string-based data."""
        try:
            json_data = json.loads(data)
            chunks = json_data.pop('chunks', []) if 'chunks' in json_data else json_data
            return BatchChunk.from_dict(chunks)
        except json.JSONDecodeError as err:
            raise SparkError.sdk('failed to parse string/bytes data as JSON', cause=err) from err
        except Exception as exc:
            raise SparkError.sdk(f'cannot create batch chunks from {data}', cause=exc) from exc


class Batches(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)
        self._base_uri = {'base_url': self.config.base_url.full, 'version': 'api/v4'}

    def describe(self):
        """Describes the batch pipeline status across the tenant."""
        url = Uri.of(None, endpoint=f'batch/status', **self._base_uri)
        return self.request(url, method='GET')

    def create(
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
            'acceptable_error_percentage': math.ceil((1 - min(accuracy or 1, 1.0)) * 100),
        }

        return self.request(url, method='POST', body={k: v for k, v in body.items() if v is not None})

    def of(self, batch_id: str) -> 'Pipeline':
        return Pipeline(batch_id, self.config)


class Pipeline(ApiResource):
    _state: str = 'open'
    _chunks: Dict[str, int] = dict()

    def __init__(self, batch_id: str, config: Config):
        super().__init__(config)
        self._id = batch_id
        self._base_uri = {'base_url': self.config.base_url.full, 'version': 'api/v4'}

        if StringUtils.is_empty(batch_id):
            error = SparkError.sdk('batch pipeline id is required to proceed', batch_id)
            self.logger.error(error.message)
            raise error

    @property
    def batch_id(self):
        return self._id

    @property
    def state(self):
        return self._state

    @property
    def stats(self):
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

    def get_info(self):
        """Retrieves the batch pipeline info."""
        url = Uri.of(None, endpoint=f'batch/{self._id}', **self._base_uri)
        return self.request(url, method='GET')

    def get_status(self):
        """Retrieves the batch pipeline status."""
        url = Uri.of(None, endpoint=f'batch/{self._id}/status', **self._base_uri)
        return self.request(url, method='GET')

    def push(
        self,
        *,
        chunks: Optional[List[BatchChunk]] = None,
        data: Optional[ChunkData] = None,
        inputs: Optional[List[Any]] = None,
        raw: Union[None, str, bytes] = None,
        if_chunk_id_duplicated: str = 'replace',  # 'ignore' | 'replace' | 'throw'
    ):
        self.__assert_state(['closed', 'cancelled'])

        url = Uri.of(None, endpoint=f'batch/{self._id}/chunks', **self._base_uri)
        body = self.__build_chunk_data(chunks, data, inputs, raw, if_chunk_id_duplicated)

        response = self.request(url, method='POST', body=body)
        total = response.data['record_submitted'] if isinstance(response.data, dict) else 0
        self.logger.info(f'pushed {total} records to batch pipeline <{self._id}>')

        return response

    def pull(self, max_chunks: int = 100):
        self.__assert_state(['cancelled'])

        endpoint = f'batch/{self._id}/chunkresults?max_chunks={max(1, max_chunks)}'

        response = self.request(Uri.of(None, endpoint=endpoint, **self._base_uri))
        total = response.data['status']['records_available'] if isinstance(response.data, dict) else 0
        self.logger.info(f'{total} available records from batch pipeline <{self._id}>')

        return response

    def dispose(self, state: str = 'closed'):
        """Disposes the batch pipeline."""
        self.__assert_state(['closed', 'cancelled'])

        url = Uri.of(None, endpoint=f'batch/{self._id}', **self._base_uri)

        response = self.request(url, method='PATCH', body={'batch_status': state})
        self.logger.info(f'batch pipeline <{self._id}> has been {state}')
        self._state = state

        return response

    def cancel(self):
        return self.dispose(state='cancelled')

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
                cause=json.dumps(cause),
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
                    self.logger.warn(
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


def create_chunks(
    dataset: List[Any],  # input dataset in json array format
    *,
    headers: Optional[List[str]] = None,  # headers for the input dataset
    chunk_size: int = 200,
    parameters: Optional[Dict[str, Any]] = None,
    summary: Optional[Dict[str, Any]] = None,
) -> List[BatchChunk]:
    """Creates a list of batch chunks from a JSON array dataset."""
    length = len(dataset)
    chunk_size = max(1, chunk_size)
    batch_size = math.ceil(length / chunk_size)

    headers = headers or (length > 0 and cast(List[str], dataset.pop(0))) or []
    if not headers:
        raise SparkError.sdk('missing headers for the input dataset', cause=dataset)

    chunks = []
    for i in range(batch_size):
        start = i * chunk_size
        end = min(start + chunk_size, length)
        inputs = [headers] + dataset[start:end]
        chunks.append(BatchChunk(get_uuid(), ChunkData(inputs, parameters or {}, summary), size=len(inputs) - 1))
    return chunks
