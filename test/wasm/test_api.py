import cspark.wasm as Hybrid


def test_execute_service_with_single_inputs(server):
    with Hybrid.Client(base_url=server.url, token='open', logger=False) as hybrid:
        response = hybrid.services.execute('hybrid/runner[0.4.2]', inputs={'data': 'test'})

    assert isinstance(response.data, dict)
    assert response.data['outputs'] == [{'result': 'test'}]
