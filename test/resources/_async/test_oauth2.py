import cspark.sdk as Spark
import pytest


@pytest.mark.anyio
async def test_get_access_token_via_oauth2(server):
    async with Spark.AsyncClient(base_url=server.url, oauth='./test/sample-ccg.txt', logger=False) as spark:
        token = await spark.config.auth.oauth.aretrieve_token(spark.config, spark.http_client)  # type: ignore

    assert token.access_token == 'fake access token'
    assert token.expires_in == 360
    assert token.token_type == 'Bearer'
