import pytest
from cspark.mcp import McpConfig, McpUrl
from cspark.sdk import BaseUrl, Config, SparkSdkError


def test_mcp_url_full_appends_mcp_path():
    url = McpUrl.of(env='uat.us', tenant='my-tenant')
    assert isinstance(url, BaseUrl)
    assert url.service == 'mcp'
    assert url.tenant == 'my-tenant'
    assert url.value == 'https://mcp.uat.us.coherent.global'
    assert url.full == 'https://mcp.uat.us.coherent.global/my-tenant/mcp'


def test_mcp_url_from_excel_base_url():
    base = BaseUrl.of(url='https://excel.test.coherent.global/my-tenant')
    url = McpUrl(base.to('mcp'), base.tenant)
    assert url.full == 'https://mcp.test.coherent.global/my-tenant/mcp'


def test_mcp_url_from_base_url_object():
    url = McpUrl.of(url=BaseUrl.of(env='prod', tenant='my-tenant'))
    assert url.full == 'https://mcp.prod.coherent.global/my-tenant/mcp'


def test_mcp_url_from_mcp_host():
    url = McpUrl('https://mcp.test.coherent.global', 'my-tenant')
    assert url.service == 'mcp'
    assert url.full == 'https://mcp.test.coherent.global/my-tenant/mcp'


def test_mcp_url_inherits_base_url_validation():
    with pytest.raises(SparkSdkError):
        McpUrl.of()
    with pytest.raises(SparkSdkError):
        McpUrl.of(env='test')
    with pytest.raises(SparkSdkError):
        McpUrl.of(url='http://localhost:8080/mcp')


def test_mcp_config_requires_bearer_or_oauth():
    with pytest.raises(SparkSdkError, match='bearer token or OAuth2'):
        McpConfig(env='test', tenant='t')


def test_mcp_config_strips_bearer_prefix_and_builds_headers():
    config = McpConfig(env='test', tenant='my-tenant', token='Bearer secret-token')
    assert isinstance(config, Config)
    assert config.auth.token == 'secret-token'
    assert config.auth.type == 'token'
    assert config.auth.as_header == {'Authorization': 'Bearer secret-token'}
    assert config.base_url.tenant == 'my-tenant'
    assert config.base_url.full == 'https://mcp.test.coherent.global/my-tenant/mcp'
    assert 'secret-token' not in str(config)


def test_mcp_config_accepts_oauth_without_retrieved_token():
    config = McpConfig(
        env='test',
        tenant='my-tenant',
        oauth={'client_id': 'id', 'client_secret': 'secret'},
    )
    assert config.auth.type == 'oauth'
    assert config.auth.token is None
    assert config.auth.oauth is not None
    assert config.auth.oauth.access_token is None


def test_mcp_config_rejects_api_key_only(monkeypatch):
    monkeypatch.setenv('CSPARK_API_KEY', 'only-api-key')
    monkeypatch.delenv('CSPARK_BEARER_TOKEN', raising=False)
    monkeypatch.delenv('CSPARK_CLIENT_ID', raising=False)
    monkeypatch.delenv('CSPARK_CLIENT_SECRET', raising=False)
    monkeypatch.delenv('CSPARK_OAUTH_PATH', raising=False)
    with pytest.raises(SparkSdkError, match='bearer token or OAuth2'):
        McpConfig(env='test', tenant='t')


def test_mcp_config_accepts_explicit_base_url():
    config = McpConfig(base_url='https://excel.test.coherent.global/my-tenant', token='tok')
    assert config.base_url.value == 'https://mcp.test.coherent.global'
    assert config.base_url.tenant == 'my-tenant'
    assert config.base_url.full == 'https://mcp.test.coherent.global/my-tenant/mcp'


def test_mcp_config_copy_with_preserves_auth():
    config = McpConfig(env='test', tenant='my-tenant', token='tok')
    copy = config.copy_with(tenant='other')
    assert isinstance(copy, McpConfig)
    assert copy.base_url.tenant == 'other'
    assert copy.base_url.full == 'https://mcp.test.coherent.global/other/mcp'
    assert copy.auth.token == 'tok'
