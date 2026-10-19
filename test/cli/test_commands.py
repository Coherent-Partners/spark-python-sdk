from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from click.testing import CliRunner

from .conftest import make_response


def test_root_help(runner: CliRunner, cli):
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    for name in ('health', 'services', 'folders', 'transforms', 'logs', 'export', 'import', 'wasm', 'files'):
        assert name in result.output


def test_health_check(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.health.check.return_value = make_response({'status': 'UP'})
    result = runner.invoke(cli, ['health', 'check'])
    assert result.exit_code == 0
    assert json.loads(result.output) == {'status': 'UP'}
    mock_client.health.check.assert_called_once()


def test_health_ok_false(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.health.ok.return_value = False
    result = runner.invoke(cli, ['health', 'ok'])
    assert result.exit_code == 1
    assert result.output.strip() == 'false'


def test_folders_create(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.folders.create.return_value = make_response({'status': 'Success', 'data': {'name': 'demo'}})
    result = runner.invoke(cli, ['folders', 'create', 'demo', '--description', 'A folder'])
    assert result.exit_code == 0
    mock_client.folders.create.assert_called_once()
    assert json.loads(result.output)['data']['name'] == 'demo'


def test_folders_exists(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.folders.exists.return_value = True
    result = runner.invoke(cli, ['folders', 'exists', 'demo'])
    assert result.exit_code == 0
    assert result.output.strip() == 'true'


def test_folders_update(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.folders.update.return_value = make_response({'status': 'Success'})
    result = runner.invoke(cli, ['folders', 'update', 'folder-id', '--description', 'Updated'])
    assert result.exit_code == 0
    mock_client.folders.update.assert_called_once_with(
        'folder-id',
        description='Updated',
        category=None,
        start_date=None,
        launch_date=None,
    )


def test_services_list_uses_sdk_request(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.services.request.return_value = make_response(
        {'data': [{'serviceName': 'pricing'}, {'serviceName': 'rating'}]}
    )
    result = runner.invoke(cli, ['services', 'list', 'demo', '--name-only'])
    assert result.exit_code == 0
    assert json.loads(result.output) == ['pricing', 'rating']
    mock_client.services.request.assert_called_once()


def test_services_schema(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.services.get_schema.return_value = make_response({'inputs': {}})
    result = runner.invoke(cli, ['services', 'schema', 'demo/pricing'])
    assert result.exit_code == 0
    mock_client.services.get_schema.assert_called_once_with('demo/pricing')


def test_services_metadata(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.services.get_metadata.return_value = make_response({'service_id': 'abc'})
    result = runner.invoke(cli, ['services', 'metadata', 'demo/pricing'])
    assert result.exit_code == 0
    assert json.loads(result.output)['service_id'] == 'abc'


def test_services_exists(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.services.exists.return_value = False
    result = runner.invoke(cli, ['services', 'exists', 'demo/missing'])
    assert result.exit_code == 1
    assert result.output.strip() == 'false'


def test_services_validate(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.services.validate.return_value = make_response({'status': 'Success'})
    result = runner.invoke(cli, ['services', 'validate', 'demo/pricing', '--inputs', '{"x": 1}'])
    assert result.exit_code == 0
    mock_client.services.validate.assert_called_once()


def test_services_create_with_progress(runner: CliRunner, cli, mock_client: MagicMock, tmp_path: Path):
    workbook = tmp_path / 'service.xlsx'
    workbook.write_bytes(b'fake-xlsx')

    compilation = MagicMock()
    compilation.initiate.return_value = make_response(
        {
            'response_data': {
                'nodegen_compilation_jobid': 'job-1',
                'original_file_documentid': 'file-1',
                'engine_file_documentid': 'engine-1',
            }
        }
    )
    compilation.get_status.return_value = make_response({'response_data': {'progress': 100, 'status': 'Success'}})
    mock_client.services.compilation = compilation
    mock_client.services.publish.return_value = make_response({'response_data': {'version_id': 'v1'}})

    result = runner.invoke(cli, ['services', 'create', 'pricing', '-f', 'demo', '--file', str(workbook)])
    assert result.exit_code == 0, result.output
    compilation.initiate.assert_called_once()
    compilation.get_status.assert_called()
    mock_client.services.publish.assert_called_once()
    # Rich spinners may mix status lines into CliRunner output; parse the JSON payload.
    json_start = result.output.index('{')
    payload = json.loads(result.output[json_start:])
    assert 'upload' in payload and 'compilation' in payload and 'publication' in payload


def test_services_download(runner: CliRunner, cli, mock_client: MagicMock, tmp_path: Path):
    out = tmp_path / 'service.xlsx'
    mock_client.services.download.return_value = make_response(buffer=b'xlsx-bytes')
    result = runner.invoke(cli, ['services', 'download', 'demo/pricing', '-o', str(out)])
    assert result.exit_code == 0
    assert out.read_bytes() == b'xlsx-bytes'


def test_services_version(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.services.get_versions.return_value = make_response([{'version': '1.0'}, {'version': '0.9'}])
    result = runner.invoke(cli, ['services', 'version', 'demo/pricing', '--latest'])
    assert result.exit_code == 0
    assert json.loads(result.output) == {'version': '1.0'}


def test_transforms_list(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.transforms.list.return_value = make_response({'response_data': []})
    result = runner.invoke(cli, ['transforms', 'list', 'demo'])
    assert result.exit_code == 0
    mock_client.transforms.list.assert_called_once_with('demo')


def test_transforms_save(runner: CliRunner, cli, mock_client: MagicMock, tmp_path: Path):
    definition = tmp_path / 'transform.json'
    definition.write_text(
        json.dumps({'schema': 'JSONtransforms_v1.0.1', 'api_version': 'v3', 'inputs': '{}', 'outputs': '{}'}),
        encoding='utf-8',
    )
    mock_client.transforms.save.return_value = make_response({'status': 'Success'})
    result = runner.invoke(cli, ['transforms', 'save', '-f', 'demo', '-n', 't1', '--file', str(definition)])
    assert result.exit_code == 0
    mock_client.transforms.save.assert_called_once()


def test_logs_get(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.logs.get.return_value = make_response({'call_id': 'c1'})
    result = runner.invoke(cli, ['logs', 'get', 'c1'])
    assert result.exit_code == 0
    assert json.loads(result.output)['call_id'] == 'c1'


def test_logs_download(runner: CliRunner, cli, mock_client: MagicMock, tmp_path: Path):
    out = tmp_path / 'logs.json'
    mock_client.logs.download.return_value = make_response(
        data={'status': 'Success'},
        buffer=b'[{"call_id":"1"}]',
    )
    result = runner.invoke(cli, ['logs', 'download', '-f', 'demo', '-s', 'pricing', '-o', str(out)])
    assert result.exit_code == 0
    assert out.read_bytes() == b'[{"call_id":"1"}]'


def test_export_describe(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.impex.exports.describe.return_value = make_response({'jobs': []})
    result = runner.invoke(cli, ['export', 'describe'])
    assert result.exit_code == 0
    assert json.loads(result.output) == {'jobs': []}


def test_export_run(runner: CliRunner, cli, mock_client: MagicMock, tmp_path: Path):
    out = tmp_path / 'export.zip'
    mock_client.impex.exp.return_value = [make_response(buffer=b'zip-bytes')]
    result = runner.invoke(cli, ['export', '--folder', 'demo', '-o', str(out)])
    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b'zip-bytes'
    mock_client.impex.exp.assert_called_once()


def test_import_run(runner: CliRunner, cli, mock_client: MagicMock, tmp_path: Path):
    package = tmp_path / 'package.zip'
    package.write_bytes(b'zip')
    mock_client.impex.imp.return_value = make_response({'status': 'completed', 'outputs': {'services': ['a']}})
    result = runner.invoke(cli, ['import', str(package), '-d', 'demo/pricing'])
    assert result.exit_code == 0, result.output
    mock_client.impex.imp.assert_called_once()


def test_export_cancel(runner: CliRunner, cli, mock_client: MagicMock):
    mock_client.impex.exports.cancel.return_value = make_response({'id': 'job-1', 'status': 'cancelled'})
    result = runner.invoke(cli, ['export', 'cancel', 'job-1'])
    assert result.exit_code == 0
    mock_client.impex.exports.cancel.assert_called_once_with('job-1')


def test_wasm_download(runner: CliRunner, cli, mock_client: MagicMock, tmp_path: Path):
    out = tmp_path / 'wasm.zip'
    mock_client.wasm.download.return_value = make_response(buffer=b'wasm')
    result = runner.invoke(cli, ['wasm', 'download', 'demo/pricing', '-o', str(out)])
    assert result.exit_code == 0
    assert out.read_bytes() == b'wasm'


def test_files_download(runner: CliRunner, cli, mock_client: MagicMock, tmp_path: Path):
    out = tmp_path / 'file.bin'
    mock_client.files.download.return_value = make_response(buffer=b'content')
    result = runner.invoke(cli, ['files', 'download', 'https://example.com/file.bin', '-o', str(out)])
    assert result.exit_code == 0
    assert out.read_bytes() == b'content'
