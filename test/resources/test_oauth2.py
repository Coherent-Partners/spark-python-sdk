import cspark.sdk as Spark
import pytest


@pytest.mark.anyio
async def test_get_access_token_via_oauth2(server):
    spark = Spark.AsyncClient(base_url=server.url, oauth='./test/sample-ccg.txt', logger=False)
    token = await spark.config.auth.oauth.async_retrieve_token(spark.config)

    assert token.access_token == 'fake access token'
    assert token.expires_in == 360
    assert token.token_type == 'Bearer'
