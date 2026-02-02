import pytest
from cspark.sdk import SparkSdkError
from cspark.wasm import DEFAULT_RUNNER_URL, RunnerUrl


def test_runner_url_can_be_created_with_default_values_if_not_provided():
    with pytest.raises(SparkSdkError):
        RunnerUrl.of()

    url = RunnerUrl()
    assert url.value == DEFAULT_RUNNER_URL
    assert url.tenant == ''
    assert url.env is None
    assert url.service is None

    url = RunnerUrl.of(url='http://localhost:8080/tenant-name')
    assert url.value == 'http://localhost:8080'
    assert url.tenant == 'tenant-name'
    assert url.env is None
    assert url.service is None

    url = RunnerUrl(url='http://localhost:8080', tenant='new-tenant')
    assert url.value == 'http://localhost:8080'
    assert url.tenant == 'new-tenant'
    assert url.env is None
    assert url.service is None
