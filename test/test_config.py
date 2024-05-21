import pytest
from cspark.sdk import BaseUrl, SparkSdkError


def test_build_base_url_from_parts():
    VALID_URL = 'https://excel.test.coherent.global/tenant'
    assert BaseUrl.of(url='https://excel.test.coherent.global/tenant').full == VALID_URL
    assert BaseUrl.of(url='https://excel.test.coherent.global', tenant='tenant').full == VALID_URL
    assert BaseUrl.of(env='test', tenant='tenant').full == VALID_URL


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
