import pytest
from cspark.sdk import BaseUrl, SparkSdkError

VALID_URL = 'https://excel.test.coherent.global/tenant'


def test_build_base_url_from_parts():
    assert BaseUrl(url='https://excel.test.coherent.global/tenant').full == VALID_URL
    assert BaseUrl(url='https://excel.test.coherent.global', tenant='tenant').full == VALID_URL
    assert BaseUrl(env='test', tenant='tenant').full == VALID_URL


def test_throw_error_when_params_are_incorrect():
    with pytest.raises(SparkSdkError):
        BaseUrl()
    with pytest.raises(SparkSdkError):
        BaseUrl(tenant='tenant')
    with pytest.raises(SparkSdkError):
        BaseUrl(env='test')


def test_throw_error_if_tenant_name_is_missing():
    with pytest.raises(SparkSdkError):
        BaseUrl(url='https://excel.test.coherent.global/')
    with pytest.raises(SparkSdkError):
        BaseUrl(env='test')


def test_throw_error_if_base_url_is_not_of_spark():
    with pytest.raises(SparkSdkError):
        BaseUrl(url='https://coherent.global')
    with pytest.raises(SparkSdkError):
        BaseUrl(url='https://coherent.global/tenant')
    with pytest.raises(SparkSdkError):
        BaseUrl(url='https://excel.test.coherent.global.net/tenant')
    with pytest.raises(SparkSdkError):
        BaseUrl(url='file://excel.test.coherent.global/tenant')
    with pytest.raises(SparkSdkError):
        BaseUrl(url='https://excel.spark.global/tenant')
