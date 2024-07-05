from cspark.sdk import SparkApiError, SparkError, SparkSdkError


def test_base_error():
    error = SparkError('sample error message')
    assert isinstance(error, Exception)
    assert repr(error) == '<SparkError>'
    assert str(error) == 'SparkError: sample error message'
    assert error.name == 'SparkError'
    assert error.message == 'sample error message'
    assert error.cause is None
    assert error.details == ''
    assert error.to_dict() == {'name': 'SparkError', 'message': 'sample error message', 'cause': None}


def test_error_of_sdk_type():
    error = SparkError.sdk(message='sample message', cause=Exception('other error'))
    assert isinstance(error, SparkSdkError)
    assert repr(error) == '<SparkSdkError>'
    assert str(error) == 'SparkSdkError: sample message (other error)'
    assert error.name == 'SparkSdkError'
    assert error.timestamp is not None
    assert error.cause is not None
    assert 'other error' in error.details


def test_error_of_api_type():
    error = SparkError.api(
        401,
        {
            'message': 'authentication required',
            'cause': {
                'request': {'url': 'url', 'method': 'GET', 'headers': {'x-request-id': 'uuidv4'}, 'body': 'data'}
            },
        },
    )
    assert isinstance(error, SparkApiError)
    assert repr(error) == '<UnauthorizedError>'
    assert 'UnauthorizedError: 401 authentication required' in str(error)
    assert error.name == 'UnauthorizedError'
    assert error.status == 401
    assert error.request_id == 'uuidv4'
