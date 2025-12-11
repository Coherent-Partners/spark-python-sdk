import cspark.sdk as Spark


def test_execute_service_with_default_inputs(server):
    with Spark.Client(base_url=server.url, api_key='open', logger=False) as spark:
        response = spark.services.execute('my-folder/my-service[0.4.2]', response_format='original')

    assert isinstance(response.data, dict)
    assert response.data['status'] == 'Success'
    assert response.data['response_data'] is not None
    assert response.data['response_data']['outputs']['my_output'] == 42


def test_execute_service_with_multiple_inputs(server):
    with Spark.Client(base_url=server.url, api_key='open', logger=False) as spark:
        response = spark.services.execute('my-folder/my-service[0.4.2]', inputs=[{'my_input': 13}, {'my_input': 14}])

    assert isinstance(response.data, dict)
    assert response.data['outputs'] == [{'my_output': 42}, {'my_output': 43}]
    assert response.data['process_time'] == [1, 2]
    assert response.data['service_id'] == 'uuid'


def test_execute_service_with_metadata(server):
    with Spark.Client(base_url=server.url, api_key='open', logger=False) as spark:
        response = spark.services.execute(
            Spark.UriParams(version_id='version_uuid', public=True),
            inputs={'single_input': 13},
            subservices=['sub1', 'sub2'],
            call_purpose='Test',
            source_system='Script',
            compiler_type='xconnector',
            active_since='2021-01-01',
            echo_inputs=True,
            downloadable=True,
            selected_outputs=['my_output'],
            correlation_id='corr_uuid',
        )

    assert isinstance(response.data, dict)
    assert response.data['outputs'] == [{'single_output': 42}]
    assert response.data['version_id'] == 'version_uuid'
