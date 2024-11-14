import pytest
from cspark.sdk import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT_IN_MS, SparkSdkError
from cspark.wasm import DEFAULT_RUNNER_URL, Client

BASE_URL = 'http://localhost:8080'
TENANT = 'tenant-name'
API_KEY = 'some-api-key'


def test_should_throw_sdk_error_if_base_url_or_authentication_is_missing():
    with pytest.raises(SparkSdkError):
        Client()
    with pytest.raises(SparkSdkError):
        Client(api_key=API_KEY)
    with pytest.raises(SparkSdkError):
        Client(base_url=f'{BASE_URL}/{TENANT}')


def test_should_throw_sdk_error_if_tenant_is_missing():
    with pytest.raises(SparkSdkError):
        Client(base_url=BASE_URL, api_key=API_KEY)


def test_should_create_client_config_from_correct_base_url_and_api_key():
    client = Client(base_url=BASE_URL, api_key=API_KEY, tenant=TENANT)
    assert client.config.base_url.value == BASE_URL
    assert client.config.base_url.tenant == TENANT
    assert client.config.auth.api_key == '********-key'


def test_can_infer_tenant_name_from_base_url():
    client = Client(base_url=f'{BASE_URL}/{TENANT}', api_key=API_KEY)
    assert client.config.base_url.value == BASE_URL
    assert client.config.base_url.tenant == TENANT
    assert client.config.auth.api_key == '********-key'


def test_can_build_base_url_from_tenant_name_only():
    client = Client(tenant=TENANT, api_key=API_KEY)
    assert client.config.base_url.value == DEFAULT_RUNNER_URL
    assert client.config.base_url.tenant == TENANT
    assert client.config.base_url.full == f'{DEFAULT_RUNNER_URL}/{TENANT}'


def test_can_be_created_with_default_values_if_not_provided():
    client = Client(base_url=BASE_URL, tenant=TENANT, api_key=API_KEY)
    assert client.config.timeout == DEFAULT_TIMEOUT_IN_MS
    assert client.config.max_retries == DEFAULT_MAX_RETRIES


def test_can_create_a_copy_with_new_values():
    client = Client(base_url=BASE_URL, tenant=TENANT, api_key=API_KEY)
    copy = client.config.copy_with(api_key='new-key', tenant='new-tenant')
    assert client.config.base_url.value == BASE_URL
    assert client.config.base_url.tenant == TENANT
    assert client.config.auth.api_key == '********-key'

    assert copy.base_url.value == BASE_URL
    assert copy.auth.api_key == '***-key'
    assert copy.base_url.tenant == 'new-tenant'
    assert copy.base_url.full == f'{BASE_URL}/new-tenant'
