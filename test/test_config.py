import sys

import pytest
from cspark.sdk import BaseUrl, Config, HealthUrl, JwtConfig, SparkSdkError
from cspark.sdk._constants import *

BASE_URL = 'https://excel.test.coherent.global'
TENANT_NAME = 'tenant-name'
API_KEY = 'some-api-key'
TOKEN = (
    'eyJhbGciOiJIUzI1NiJ9.'
    'eyJpc3MiOiJodHRwczovL2tleWNsb2FrLm15LWVudi5jb2hlcmVudC5nbG9iYWwvYXV0aC9yZWFsbXMvbXktdGVuYW50IiwicmVhbG0iOiJteS10ZW5hbnQifQ.'
    '9G0zF-XAN9EpDLu11tmqkRwNFU52ecoGz4vTq0NEJBw'
)  # this unsigned token uses HS256 algorithm for testing but Coherent uses RS256 algorithm.


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
    copy = config.copy_with(api_key='new-key', tenant='new-tenant', env='prod')
    assert config.base_url.value == BASE_URL
    assert config.base_url.tenant == TENANT_NAME
    assert config.auth.api_key == '********-key'

    assert isinstance(copy, Config)
    assert copy.base_url.value == 'https://excel.prod.coherent.global'
    assert copy.auth.api_key == '***-key'
    assert copy.base_url.tenant == 'new-tenant'


def test_jwt_config_can_decode_token_to_basic_client_options():
    if sys.version_info < (3, 8):
        pytest.skip('skip this test for Python 3.7 and below')

    decoded = JwtConfig.decode(TOKEN, verify=False)
    assert decoded['token'] == TOKEN
    assert decoded['base_url'] == 'https://excel.my-env.coherent.global'
    assert decoded['tenant'] == 'my-tenant'
    assert decoded['verified'] is False
    assert isinstance(decoded['decoded'], dict)
    assert 'iss' in decoded['decoded']
    assert 'realm' in decoded['decoded']


def test_jwt_config_can_build_client_config_from_token():
    if sys.version_info < (3, 8):
        pytest.skip('skip this test for Python 3.7 and below')

    config = JwtConfig(TOKEN, verify=False, max_retries=2, retry_interval=5)
    assert config.base_url.value == 'https://excel.my-env.coherent.global'
    assert config.base_url.tenant == 'my-tenant'
    assert config.auth.token == TOKEN
    assert config.timeout == DEFAULT_TIMEOUT_IN_MS
    assert config.max_retries == 2
    assert config.retry_interval == 5
    assert config.has_headers is False


def test_jwt_config_should_throw_error_if_token_is_invalid():
    with pytest.raises(SparkSdkError):
        JwtConfig(token='invalid-token', verify=False)
    with pytest.raises(SparkSdkError):
        JwtConfig.decode('invalid-token', verify=False, raise_if_invalid=True)


def test_jwt_config_cannot_decode_invalid_token():
    decoded = JwtConfig.decode('invalid-token', verify=False)
    assert decoded['token'] == 'invalid-token'
    assert decoded['base_url'] is None
    assert decoded['tenant'] is None
    assert decoded['verified'] is False
    assert isinstance(decoded['decoded'], str)
    assert decoded['decoded'].startswith('invalid token')


def test_build_base_url_from_parts():
    VALID_URL = 'https://excel.my.env.coherent.global/tenant'
    assert BaseUrl.of(url='https://excel.my.env.coherent.global///', tenant='tenant').full == VALID_URL
    assert BaseUrl.of(url='https://excel.my.env.coherent.global/tenant').full == VALID_URL
    assert BaseUrl.of(url='https://spark.my.env.coherent.global/tenant').full == VALID_URL
    assert BaseUrl.of(url='https://excel.my.env.coherent.global', tenant='tenant').full == VALID_URL
    assert BaseUrl.of(url='https://spark.my.env.coherent.global', tenant='tenant').full == VALID_URL
    assert BaseUrl.of(env='my.env', tenant='tenant').full == VALID_URL


def test_build_base_url_from_custom_location():
    assert BaseUrl.at('my.env/tenant').full == 'https://excel.my.env.coherent.global/tenant'
    assert BaseUrl.at('my.env/tenant/other/path').full == 'https://excel.my.env.coherent.global/tenant/other/path'
    assert BaseUrl.at('my.env:tenant', separator=':').full == 'https://excel.my.env.coherent.global/tenant'
    with pytest.raises(SparkSdkError):
        BaseUrl.at(None)  # type: ignore
    with pytest.raises(SparkSdkError):
        BaseUrl.at('')
    with pytest.raises(SparkSdkError):
        BaseUrl.at('env/')
    with pytest.raises(SparkSdkError):
        BaseUrl.at('env:tenant')


def test_base_url_can_be_converted_to_other_services():
    base_url = BaseUrl.of(url='https://spark.my.env.coherent.global/tenant')  # 'spark' is not a supported service name
    assert base_url.full == 'https://excel.my.env.coherent.global/tenant'
    assert base_url.to('utility', with_tenant=True) == 'https://utility.my.env.coherent.global/tenant'
    assert base_url.to('keycloak', with_tenant=False) == 'https://keycloak.my.env.coherent.global'
    assert base_url.oauth2 == 'https://keycloak.my.env.coherent.global/auth/realms/tenant'


def test_copy_base_url_with_new_values():
    base_url = BaseUrl.of(url='https://excel.my.env.coherent.global/tenant')
    assert base_url.copy_with().full == 'https://excel.my.env.coherent.global/tenant'
    assert base_url.copy_with(env='new-env').full == 'https://excel.new-env.coherent.global/tenant'
    assert base_url.copy_with(tenant='new-tenant').full == 'https://excel.my.env.coherent.global/new-tenant'
    assert (
        base_url.copy_with(env='new-env', tenant='new-tenant').full
        == 'https://excel.new-env.coherent.global/new-tenant'
    )
    assert (
        base_url.copy_with(url='https://excel.new-env.coherent.global').full
        == 'https://excel.new-env.coherent.global/tenant'
    )
    assert (
        base_url.copy_with(url='https://excel.new-env.coherent.global', tenant='new-tenant').full
        == 'https://excel.new-env.coherent.global/new-tenant'
    )


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


def test_health_url_can_build_from_different_parts():
    VALID_URL, TENANT = 'https://excel.my.env.coherent.global', 'tenant'
    SPARK_URL = f'https://spark.test.coherent.global/{TENANT}'

    # from environment name
    assert HealthUrl.when('my.env').value == VALID_URL
    assert HealthUrl.when('test').value == 'https://excel.test.coherent.global'

    # from URL string
    assert HealthUrl.when(VALID_URL).value == VALID_URL
    assert HealthUrl.when(f'{VALID_URL}/{TENANT}').value == VALID_URL
    assert HealthUrl.when(SPARK_URL).value == 'https://excel.test.coherent.global'

    # from BaseUrl object
    assert HealthUrl.when(BaseUrl.of(url=VALID_URL, tenant=TENANT)).value == VALID_URL
    assert HealthUrl.when(BaseUrl.of(url=f'{VALID_URL}/{TENANT}')).value == VALID_URL
    assert HealthUrl.when(BaseUrl.of(url=SPARK_URL)).value == 'https://excel.test.coherent.global'
