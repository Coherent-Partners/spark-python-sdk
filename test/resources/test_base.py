from cspark.sdk import Uri, UriParams

BASE_URL = 'https://excel.test.coherent.global/tenant-name'


def test_build_url_from_partial_resources():
    assert (
        Uri.partial('folders/f/services/s', base_url=BASE_URL, endpoint='execute').value
        == 'https://excel.test.coherent.global/tenant-name/api/v3/folders/f/services/s/execute'
    )
    assert (
        Uri.partial('proxy/custom-endpoint', base_url=BASE_URL).value
        == 'https://excel.test.coherent.global/tenant-name/api/v3/proxy/custom-endpoint'
    )


def test_handle_extra_slashes_in_partial_resources():
    assert (
        Uri.partial('/folders/f/services/s/', base_url=BASE_URL, endpoint='execute').value
        == 'https://excel.test.coherent.global/tenant-name/api/v3/folders/f/services/s/execute'
    )
    assert (
        Uri.partial('/public/version/123/', base_url=BASE_URL).value
        == 'https://excel.test.coherent.global/tenant-name/api/v3/public/version/123'
    )


def test_build_url_from_uri_params():
    assert (
        Uri.of(UriParams(folder='f', service='s'), base_url=BASE_URL, endpoint='execute').value
        == 'https://excel.test.coherent.global/tenant-name/api/v3/folders/f/services/s/execute'
    )
    assert (
        Uri.of(None, base_url=BASE_URL, version='api/v4', endpoint='execute').value
        == 'https://excel.test.coherent.global/tenant-name/api/v4/execute'
    )
    assert (
        Uri.of(UriParams(public=True), base_url=BASE_URL, version='api/v4', endpoint='execute').value
        == 'https://excel.test.coherent.global/tenant-name/api/v4/public/execute'
    )
    assert (
        Uri.of(
            UriParams(folder='high', service='priority', version_id='low-priority'),
            base_url=BASE_URL,
            endpoint='execute',
        ).value
        == 'https://excel.test.coherent.global/tenant-name/api/v3/folders/high/services/priority/execute'
    )
    assert (
        Uri.of(UriParams(proxy='custom-endpoint'), base_url=BASE_URL).value
        == 'https://excel.test.coherent.global/tenant-name/api/v3/proxy/custom-endpoint'
    )
    assert (
        Uri.of(UriParams(proxy='custom-endpoint', public=True), base_url=BASE_URL).value
        == 'https://excel.test.coherent.global/tenant-name/api/v3/public/proxy/custom-endpoint'
    )
    assert (
        Uri.of(UriParams(proxy='/custom-endpoint///', public=True), base_url=BASE_URL).value
        == 'https://excel.test.coherent.global/tenant-name/api/v3/public/proxy/custom-endpoint'
    )


def test_decode_string_uri():
    assert Uri.decode('folders/f/services/s') == UriParams(folder='f', service='s')
    assert Uri.decode('f/s') == UriParams(folder='f', service='s')
    assert Uri.decode('f/s[1.0]') == UriParams(folder='f', service='s', version='1.0')
    assert Uri.decode('folders/f/services/s[1.2.3]') == UriParams(folder='f', service='s', version='1.2.3')
    assert Uri.decode('service/456') == UriParams(service_id='456')
    assert Uri.decode('version/123') == UriParams(version_id='123')
    assert Uri.decode('/f/s/') == UriParams(folder='f', service='s')
    assert Uri.decode('f/s/') == UriParams(folder='f', service='s')
    assert Uri.decode('///f//s//') == UriParams(folder='f', service='s')
    assert Uri.decode('/f/s[]/') == UriParams(folder='f', service='s')
    assert Uri.decode('') == UriParams()
    assert Uri.decode('//f/') == UriParams()
    assert Uri.decode('//f') == UriParams()
    assert Uri.decode('///') == UriParams()
