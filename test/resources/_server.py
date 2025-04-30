import asyncio
import json
import threading
import time
import typing

from cspark.sdk import BaseUrl
from uvicorn.server import Server

Message = typing.Dict[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[typing.Dict[str, typing.Any]], typing.Coroutine[None, None, None]]
Scope = typing.Dict[str, typing.Any]


async def router(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope['type'] == 'http'

    # all requests must have at least these headers: x-tenant-name, x-request-id, x-spark-ua
    headers = {k.decode(): v.decode() for k, v in scope['headers']}
    assert 'x-tenant-name' in headers
    assert 'x-request-id' in headers
    assert 'x-spark-ua' in headers

    if scope['path'] == '/my-tenant/api/v3/folders/my-folder/services/my-service/execute':
        await service_execute_v3(scope, receive, send)
    elif scope['path'] == '/my-tenant/api/v4/execute':
        await service_execute_v4(scope, receive, send)
    elif scope['path'] == '/my-tenant/api/v3/public/version/version_uuid':
        await service_execute_with_metadata(scope, receive, send)
    elif scope['path'] == '/my-tenant/api/v4/batch':
        await batch_create(scope, receive, send)
    elif scope['path'] == '/my-tenant/api/v4/batch/batch_uuid/chunks':
        await batch_push(scope, receive, send)
    elif scope['path'] == '/my-tenant/api/v4/batch/batch_uuid/chunkresults':
        await batch_pull(scope, send)
    elif scope['path'] == '/my-tenant/api/v4/batch/batch_uuid':
        await batch_dispose(scope, receive, send)
    else:
        await send({'type': 'http.response.start', 'status': 404, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'Resource not defined yet'})


async def read_body(receive):
    """Read and return the entire body from an incoming ASGI message."""
    body = b''
    more_body = True

    while more_body:
        message = await receive()
        body += message.get('body', b'')
        more_body = message.get('more_body', False)

    return body


async def service_execute_v3(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope['method'] == 'POST'

    req_body = json.loads(await read_body(receive))
    assert req_body['request_data'] == {'inputs': {}}
    assert req_body['request_meta']['version'] == '0.4.2'
    assert req_body['request_meta']['call_purpose'] == 'Single Execution'
    assert req_body['request_meta']['compiler_type'] == 'Neuron'
    assert req_body['request_meta']['source_system'] == 'Spark Python SDK'

    res_body = '{"status":"Success","response_data":{"outputs":{"my_output":42}},"response_meta":{},"error": null}'
    await send({'type': 'http.response.start', 'status': 200, 'headers': [[b'content-type', b'application/json']]})
    await send({'type': 'http.response.body', 'body': res_body.encode()})


async def service_execute_v4(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope['method'] == 'POST'

    req_body = json.loads(await read_body(receive))
    assert len(req_body['inputs']) == 2
    assert req_body['service'] == 'my-folder/my-service[0.4.2]'
    assert req_body['call_purpose'] == 'Sync Batch Execution'
    assert req_body['source_system'] == 'Spark Python SDK'

    res_body = '{"outputs": [{"my_output": 42}, {"my_output": 43}], "process_time": [1, 2], "service_id": "uuid"}'
    # Note that Spark may return more headers.
    await send({'type': 'http.response.start', 'status': 200, 'headers': [[b'content-type', b'application/json']]})
    await send({'type': 'http.response.body', 'body': res_body.encode()})


async def service_execute_with_metadata(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope['method'] == 'POST'

    req_body = json.loads(await read_body(receive))
    req_meta = req_body['request_meta']
    assert req_body['request_data']['inputs'] == {'single_input': 13}
    assert req_meta['version_id'] == 'version_uuid'
    assert req_meta['call_purpose'] == 'Test'
    assert req_meta['compiler_type'] == 'Xconnector'
    assert req_meta['source_system'] == 'Script'
    assert req_meta['transaction_date'] == '2021-01-01'
    assert req_meta['service_category'] == 'sub1,sub2'
    assert req_meta['excel_file'] is True
    assert req_meta['response_data_inputs'] is True
    assert req_meta['requested_output'] == 'my_output'
    assert req_meta['correlation_id'] == 'corr_uuid'

    res_body = '{"status":"Success","response_data":{"outputs":{"single_output":42}},"response_meta":{"version_id":"version_uuid"},"error": null}'
    await send({'type': 'http.response.start', 'status': 200, 'headers': [[b'content-type', b'application/json']]})
    await send({'type': 'http.response.body', 'body': res_body.encode()})


async def batch_create(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope['method'] == 'POST'

    req_body = json.loads(await read_body(receive))
    assert req_body['service'] == 'f/s'
    assert req_body['call_purpose'] == 'Async Batch Execution'
    assert req_body['source_system'] == 'Spark Python SDK'
    assert req_body['initial_workers'] == 100
    assert req_body['runner_thread_count'] == 4
    assert req_body['acceptable_error_percentage'] == 10

    res_body = '{"object": "batch", "id": "batch_uuid", "data": {}}'
    await send({'type': 'http.response.start', 'status': 200, 'headers': [[b'content-type', b'application/json']]})
    await send({'type': 'http.response.body', 'body': res_body.encode()})


async def batch_push(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope['method'] == 'POST'

    req_body = json.loads(await read_body(receive))
    assert len(req_body['chunks']) > 0

    res_body = '{"batch_status": "in_progress", "record_submitted": 3, "records_available": 0}'  # and more...
    await send({'type': 'http.response.start', 'status': 200, 'headers': [[b'content-type', b'application/json']]})
    await send({'type': 'http.response.body', 'body': res_body.encode()})


async def batch_pull(scope: Scope, send: Send) -> None:
    assert scope['method'] == 'GET'
    query_params = dict(q.split(b'=') for q in scope['query_string'].split(b'&') if q)
    assert b'max_chunks' in query_params and query_params[b'max_chunks'] == b'2'

    res_body = '{"data":[{"outputs": [{}, {}]}, {"outputs": [{}]}], "status": {"records_available": 0}}'
    await send({'type': 'http.response.start', 'status': 200, 'headers': [[b'content-type', b'application/json']]})
    await send({'type': 'http.response.body', 'body': res_body.encode()})


async def batch_dispose(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope['method'] == 'PATCH'

    req_body = json.loads(await read_body(receive))
    assert req_body['batch_status'] == 'closed'

    res_body = '{"object": "batch", "id": "batch_uuid", "meta": {}}'
    await send({'type': 'http.response.start', 'status': 200, 'headers': [[b'content-type', b'application/json']]})
    await send({'type': 'http.response.body', 'body': res_body.encode()})


class LocalServer(Server):
    # A simple local server for testing purposes.
    # Inspired by httpx's TestServer (https://github.com/encode/httpx/blob/master/tests/conftest.py)

    @property
    def url(self) -> BaseUrl:
        return BaseUrl(url=f'http://{self.config.host}:{self.config.port}', tenant='my-tenant')

    @property
    def hostname(self) -> str:
        return self.config.host

    @property
    def port(self) -> int:
        return self.config.port

    def install_signal_handlers(self) -> None:
        # Disable the default installation of handlers for signals such as SIGTERM,
        # because it can only be done in the main thread.
        pass

    async def serve(self, sockets=None):
        self.restart_requested = asyncio.Event()

        loop = asyncio.get_event_loop()
        tasks = {
            loop.create_task(super().serve(sockets=sockets)),
            loop.create_task(self.watch_restarts()),
        }
        await asyncio.wait(tasks)

    async def restart(self) -> None:
        # This coroutine may be called from a different thread than the one the
        # server is running on, and from an async environment that's not asyncio.
        # For this reason, we use an event to coordinate with the server
        # instead of calling shutdown()/startup() directly, and should not make
        # any asyncio-specific operations.
        self.started = False
        self.restart_requested.set()
        while not self.started:
            await asyncio.sleep(0.2)

    async def watch_restarts(self) -> None:
        while True:
            if self.should_exit:
                return

            try:
                await asyncio.wait_for(self.restart_requested.wait(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

            self.restart_requested.clear()
            await self.shutdown()
            await self.startup()


def serve_in_thread(server: LocalServer) -> typing.Iterator[LocalServer]:
    thread = threading.Thread(target=server.run)
    thread.start()
    try:
        while not server.started:
            time.sleep(1e-3)
        yield server
    finally:
        server.should_exit = True
        thread.join()
