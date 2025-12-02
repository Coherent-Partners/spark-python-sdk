import json
import logging
import pathlib
import re
import sys

import cspark.sdk as Spark
import jsonschema
import yaml

logging.basicConfig(filename='console.log', filemode='w', format=Spark.DEFAULT_LOGGER_FORMAT)
logger = Spark.get_logger(context='Bulk Upload')


class ConfigError(ValueError):
    """Inappropriate configuration values."""

    ...


def load_config(file: pathlib.Path = pathlib.Path('config.yml')) -> dict:
    try:
        if not file.exists():
            raise ConfigError(f'file not found: {file}')

        with file.open() as f:
            config = yaml.safe_load(f) if file.suffix.lower() in ['.yml', '.yaml'] else json.load(f)

        with pathlib.Path('schema.json').open() as f:
            schema = json.load(f)
            jsonschema.validate(instance=config, schema=schema)

        if not re.match(r'^1\.\d+$', str(config.get('version'))):  # should match: 1.*
            raise ConfigError(f'unsupported version (must be 1.*)')

        config['logging'] = getattr(logging, config.get('logging', 'INFO'))
        config['services'] = extract_services(config)
        return config
    except (yaml.YAMLError, json.JSONDecodeError, jsonschema.ValidationError, ConfigError) as err:
        logger.error(f'invalid configuration: {file}\n{err!s}')
        sys.exit(1)


def extract_services(config: dict) -> list[dict]:
    formats = config.get('allowed_formats', ['.xlsx', '.xls'])
    file_size = config.get('max_file_size_mb', 25) * 1024 * 1024
    upload_cfg = config.get(
        'upload',
        {
            'versioning': 'patch',
            'track_user': True,
            'max_retries': 3,
            'retry_interval': 3.0,
        },
    )

    services = []
    for svc in config.get('services', []):
        if isinstance(svc, str):
            svc = {'name': None, 'file': svc}

        if isinstance(svc, dict):
            svc['using'] = {**upload_cfg, **svc.get('using', {})}
            if not svc['using'].get('folder'):  # type: ignore
                logger.warning(f'folder name is required for service: {svc.get("name")}')
                continue

            file = pathlib.Path(svc['file'])
            if not (file.exists() and file.suffix in formats):
                logger.warning(f'incorrect service file: {svc["file"]}')
                continue
            if file.stat().st_size > file_size:
                logger.warning(f'file size is too large: {file.name}')
                continue

            svc.update({'name': svc.get('name') or file.stem, 'file_name': file.name})
        services.append(svc)

    logger.info(f'found {len(services)} service(s) to upload')

    return services
