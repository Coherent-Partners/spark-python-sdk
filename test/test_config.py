import pytest
from cspark.sdk import BaseUrl, Config, SparkSdkError
from cspark.sdk._constants import *

BASE_URL = 'https://excel.test.coherent.global'
TENANT_NAME = 'tenant-name'
API_KEY = 'some-api-key'


def test_throw_sdk_error_if_base_url_or_auth_is_missing():
    with pytest.raises(SparkSdkError):
        Config()
    with pytest.raises(SparkSdkError):
        Config(api_key='some key')
    with pytest.raises(SparkSdkError):
        Config(base_url=f'{BASE_URL}/{TENANT_NAME}')


def test_throw_sdk_error_if_tenant_is_missing():
    with pytest.raises(SparkSdkError):
        Config(base_url=BASE_URL, api_key='some key')
    with pytest.raises(SparkSdkError):
        Config(env='test', api_key='some key')


def test_create_client_config_from_correct_base_url_and_api_key():
    config = Config(base_url=BASE_URL, api_key=API_KEY, tenant=TENANT_NAME)
    assert config.base_url.value == BASE_URL
    assert config.base_url.tenant == TENANT_NAME
    assert config.auth.api_key == '********-key'


def test_infer_tenant_name_from_base_url():
    config = Config(base_url=f'{BASE_URL}/{TENANT_NAME}', api_key=API_KEY)
    assert config.base_url.value == BASE_URL
    assert config.base_url.tenant == TENANT_NAME
    assert config.auth.api_key == '********-key'


def test_build_base_url_from_other_url_parts():
    config = Config(tenant=TENANT_NAME, env='test', api_key=API_KEY)
    assert config.base_url.value == BASE_URL
    assert config.base_url.tenant == TENANT_NAME
    assert config.auth.api_key == '********-key'


def test_created_with_default_values_if_not_provided():
    config = Config(base_url=f'{BASE_URL}/{TENANT_NAME}', api_key=API_KEY)
    assert config.timeout == DEFAULT_TIMEOUT_IN_MS
    assert config.max_retries == DEFAULT_MAX_RETRIES
    assert config.retry_interval == DEFAULT_RETRY_INTERVAL
    assert config.has_headers is False


def test_copied_with_new_values():
    config = Config(base_url=f'{BASE_URL}/{TENANT_NAME}', api_key=API_KEY)
    new_config = config.copy_with(api_key='new-key', tenant='new-tenant')
    assert new_config is not None
    assert new_config.base_url.value == BASE_URL
    assert new_config.auth.api_key == '***-key'
    assert new_config.base_url.tenant == 'new-tenant'


def test_build_base_url_from_parts():
    VALID_URL = 'https://excel.my.env.coherent.global/tenant'
    assert BaseUrl.of(url='https://excel.my.env.coherent.global/tenant').full == VALID_URL
    assert BaseUrl.of(url='https://spark.my.env.coherent.global/tenant').full == VALID_URL
    assert BaseUrl.of(url='https://excel.my.env.coherent.global', tenant='tenant').full == VALID_URL
    assert BaseUrl.of(url='https://spark.my.env.coherent.global', tenant='tenant').full == VALID_URL
    assert BaseUrl.of(env='my.env', tenant='tenant').full == VALID_URL


def test_throw_error_when_params_are_incorrect():
    with pytest.raises(SparkSdkError):
        BaseUrl.of()
    with pytest.raises(SparkSdkError):
        BaseUrl.of(tenant='tenant')
    with pytest.raises(SparkSdkError):
        BaseUrl.of(env='test')


def test_throw_error_if_tenant_name_is_missing():
    with pytest.raises(SparkSdkError):
        BaseUrl.of(url='https://excel.test.coherent.global/')
    with pytest.raises(SparkSdkError):
        BaseUrl.of(env='test')


def test_throw_error_if_base_url_is_not_of_spark():
    with pytest.raises(SparkSdkError):
        BaseUrl.of(url='https://coherent.global')
    with pytest.raises(SparkSdkError):
        BaseUrl.of(url='https://coherent.global/tenant')
    with pytest.raises(SparkSdkError):
        BaseUrl.of(url='https://excel.test.coherent.global.net/tenant')
    with pytest.raises(SparkSdkError):
        BaseUrl.of(url='file://excel.test.coherent.global/tenant')
    with pytest.raises(SparkSdkError):
        BaseUrl.of(url='https://excel.spark.global/tenant')
