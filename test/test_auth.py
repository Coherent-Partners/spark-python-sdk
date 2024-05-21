import pytest
from cspark.sdk import Authorization, SparkSdkError
from cspark.sdk.auth import OAuth

TOKEN = 'some-access-token'
API_KEY = 'some-api-key'
OAUTH = {'client_id': 'some-id', 'client_secret': 'some-secret'}


def test_create_open_authorization():
    assert Authorization(api_key='open').is_open is True
    assert Authorization(token='open').is_open is True


def test_create_authorization_with_api_key():
    auth = Authorization(api_key=API_KEY)
    assert auth.api_key == '********-key'
    assert auth.is_empty is False
    assert auth.is_open is False
    assert auth.type == 'api_key'
    assert auth.as_header == {'x-synthetic-key': API_KEY}
    assert auth.oauth is None
    assert auth.token is None


def test_create_authorization_with_bearer_token():
    auth = Authorization(token='Bearer ' + TOKEN)
    assert auth.token == TOKEN
    assert auth.is_empty is False
    assert auth.is_open is False
    assert auth.type == 'token'
    assert auth.as_header == {'Authorization': f'Bearer {TOKEN}'}
    assert auth.api_key is None
    assert auth.oauth is None

    assert Authorization(token=TOKEN).as_header == {'Authorization': f'Bearer {TOKEN}'}


def test_create_authorization_with_json_oauth():
    auth = Authorization(oauth=OAUTH)
    assert isinstance(auth.oauth, OAuth)
    assert auth.oauth.client_id == OAUTH['client_id']
    assert auth.oauth.client_secret == '*******cret'
    assert auth.is_empty is False
    assert auth.is_open is False
    assert auth.type == 'oauth'
    assert auth.api_key is None
    assert auth.token is None


def test_create_authorization_with_file_oauth():
    auth = Authorization(oauth='./test/sample-ccg.txt')
    assert isinstance(auth.oauth, OAuth)
    assert auth.oauth.client_id == OAUTH['client_id']
    assert auth.oauth.client_secret == '*******cret'
    assert auth.is_empty is False
    assert auth.is_open is False
    assert auth.type == 'oauth'
    assert auth.api_key is None
    assert auth.token is None


def test_throw_sdk_error_if_no_authentication_method_is_provided():
    with pytest.raises(SparkSdkError):
        Authorization()
