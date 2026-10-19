from __future__ import annotations

import json
from pathlib import Path

from cspark.cli._commands._api import (
    echo_json,
    json_parse,
    parse_pairs,
    read_json_input,
    write_bytes,
)


def test_parse_pairs_with_type_inference():
    assert parse_pairs(['a:1', 'b:true', 'c:3.5', 'd:hello'], infer_type=True) == {
        'a': 1,
        'b': True,
        'c': 3.5,
        'd': 'hello',
    }


def test_json_parse_fallback():
    assert json_parse(None) == {}
    assert json_parse('not-json', fallback={'ok': True}) == {'ok': True}
    assert json_parse('{"a": 1}') == {'a': 1}


def test_read_json_input_from_file(tmp_path: Path):
    path = tmp_path / 'data.json'
    path.write_text('{"folder": "demo"}', encoding='utf-8')
    assert read_json_input(file=path) == {'folder': 'demo'}


def test_write_bytes(tmp_path: Path):
    path = write_bytes(b'hello', tmp_path / 'out.bin')
    assert path.read_bytes() == b'hello'


def test_echo_json(capsys):
    echo_json({'a': 1})
    assert json.loads(capsys.readouterr().out) == {'a': 1}
