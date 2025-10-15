import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# Usage:
#   export CSPARK_API_KEY=...
#   python3 check_status.py --base-url 'https://excel.uat.us.coherent/global/my-tenant'


def print_separator(char: str = '-', width: int = 100) -> None:
    print(char * width)


def build_url(base_url: str, endpoint: str) -> str:
    sanitized_base = base_url.rstrip('/')
    sanitized_endpoint = endpoint if endpoint.startswith('/') else f'/{endpoint}'
    return f'{sanitized_base}{sanitized_endpoint}'


def safe_get(mapping: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    current: Any = mapping
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def bytes_to_megabytes(num_bytes: Optional[float]) -> Optional[float]:
    if num_bytes is None:
        return None
    return float(num_bytes) / (1024.0 * 1024.0)


def format_mb(value: Optional[float]) -> str:
    if value is None:
        return '-'
    return f'{value:,.2f} MB'


def percentage(numerator: Optional[float], denominator: Optional[float]) -> str:
    if numerator is None or denominator in (None, 0):
        return '-'
    return f'{(numerator / denominator) * 100:,.2f}%'


def ms_to_hms(ms: Optional[float]) -> str:
    if ms is None:
        return '-'
    seconds = float(ms) / 1000.0
    minutes, seconds = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    parts: List[str] = []
    if hours:
        parts.append(f'{hours}h')
    if minutes:
        parts.append(f'{minutes}m')
    parts.append(f'{seconds}s')
    return ' '.join(parts)


def fetch_status(
    url: str,
    token: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout_seconds: int = 15,
    verify_tls: bool = True,
) -> Dict[str, Any]:
    # Ensure exactly one auth method is provided
    if bool(token) == bool(api_key):  # both set or both empty
        raise ValueError('Provide exactly one authentication method: Bearer token or API key')

    headers = {
        'Accept': 'application/json',
        'User-Agent': 'spark-batch-status-check/1.0',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    else:
        parsed_url = urlparse(url.rstrip('/'))
        url_paths = str(parsed_url.path).split('/')
        if len(url_paths) < 2:
            raise ValueError('tenant name is missing from the base URL')
        headers['x-tenant-name'] = url_paths[1]
        headers['x-synthetic-key'] = str(api_key)

    response = requests.get(url, headers=headers, timeout=timeout_seconds, verify=verify_tls)
    response.raise_for_status()
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise ValueError(f'Response was not valid JSON: {exc}') from exc


def print_tenant_buffers(payload: Dict[str, Any]) -> None:
    configuration = safe_get(payload, ['tenant', 'configuration'], {}) or {}
    status = safe_get(payload, ['tenant', 'status'], {}) or {}

    input_allocated_bytes = configuration.get('input_buffer_allocated_bytes')
    output_allocated_bytes = configuration.get('output_buffer_allocated_bytes')

    input_used_bytes = status.get('input_buffer_used_bytes')
    output_used_bytes = status.get('output_buffer_used_bytes')

    input_remaining_bytes = status.get('input_buffer_remaining_bytes')
    output_remaining_bytes = status.get('output_buffer_remaining_bytes')

    input_allocated_mb = bytes_to_megabytes(input_allocated_bytes)
    output_allocated_mb = bytes_to_megabytes(output_allocated_bytes)

    input_used_mb = bytes_to_megabytes(input_used_bytes)
    output_used_mb = bytes_to_megabytes(output_used_bytes)

    input_remaining_mb = bytes_to_megabytes(input_remaining_bytes)
    output_remaining_mb = bytes_to_megabytes(output_remaining_bytes)

    print_separator('-', 100)
    print('Tenant Buffers')
    print(f'  Workers: {status.get("workers_in_use")} / {configuration.get("max_workers")}')
    print(f'  Inputs:')
    print(f'    - allocated: {format_mb(input_allocated_mb)}')
    print(f'    - used:      {format_mb(input_used_mb)} ({percentage(input_used_mb, input_allocated_mb)})')
    print(f'    - remaining: {format_mb(input_remaining_mb)} ({percentage(input_remaining_mb, input_allocated_mb)})')
    print(f'  Outputs:')
    print(f'    - allocated: {format_mb(output_allocated_mb)}')
    print(f'    - used:      {format_mb(output_used_mb)} ({percentage(output_used_mb, output_allocated_mb)})')
    print(f'    - remaining: {format_mb(output_remaining_mb)} ({percentage(output_remaining_mb, output_allocated_mb)})')
    print_separator('-', 100)


def print_batches(title: str, batches: List[Dict[str, Any]], limit: Optional[int] = None) -> None:
    print(title)
    if not batches:
        print('  none')
        print_separator('-', 100)
        return

    display = batches[:limit] if limit else batches
    for idx, batch in enumerate(display, start=1):
        batch_id = batch.get('id') or '-'
        data = batch.get('data') or {}
        batch_status = data.get('batch_status') or '-'
        pipeline_status = data.get('pipeline_status') or '-'
        created_by = data.get('created_by') or '-'
        created_ts = data.get('created_timestamp') or '-'
        updated_ts = data.get('updated_timestamp') or '-'
        service_uri = data.get('service_uri') or '-'
        summary = data.get('summary') or {}

        submitted = summary.get('records_submitted')
        failed = summary.get('records_failed')
        completed = summary.get('records_completed')
        compute_time_ms = summary.get('compute_time_ms')
        batch_time_ms = summary.get('batch_time_ms')

        print(f'  {idx}. id     : {batch_id}')
        print(f'     status : batch={batch_status}, pipeline={pipeline_status}')
        print(f'     service: {service_uri}')
        print(f'     created: {created_ts} by {created_by}')
        print(f'     updated: {updated_ts}')
        if summary:
            print(
                f'     summary: submitted={submitted}, completed={completed}, failed={failed}, '
                f'compute={ms_to_hms(compute_time_ms)}, total={ms_to_hms(batch_time_ms)}'
            )
        print('')

    if limit and len(batches) > limit:
        print(f'  ... and {len(batches) - limit} more')
    print_separator('-', 100)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Check and summarize Spark batch status via REST API',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--base-url',
        help='Base URL for the tenant (e.g. https://excel.my-env.coherent/global/my-tenant)',
        default=os.environ.get('CSPARK_BASE_URL'),
    )
    auth_group = parser.add_mutually_exclusive_group()
    auth_group.add_argument(
        '--token',
        default=os.environ.get('CSPARK_BEARER_TOKEN'),
        help='Bearer token; can also be provided via CSPARK_BEARER_TOKEN env var',
    )
    auth_group.add_argument(
        '--api-key',
        dest='api_key',
        default=os.environ.get('CSPARK_API_KEY'),
        help='API key; can also be provided via CSPARK_API_KEY env var. Uses header x-synthetic-key',
    )
    parser.add_argument('--limit', type=int, default=10, help='Max recent/in-progress batches to display')
    parser.add_argument('--timeout', type=int, default=30, help='HTTP request timeout (seconds)')
    parser.add_argument('--insecure', action='store_true', help='Disable TLS certificate verification')
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if not args.token and not args.api_key:
        print(
            'Error: missing credentials. Provide --token (or CSPARK_BEARER_TOKEN) or --api-key (or CSPARK_API_KEY).',
            file=sys.stderr,
        )
        return 2

    url = build_url(args.base_url, '/api/v4/batch/status')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print_separator('=', 100)
    print(f'Spark Batch Status Summary | {now}')
    print(f'URL: {url}')
    print_separator('=', 100)

    try:
        payload = fetch_status(
            url,
            token=args.token,
            api_key=args.api_key,
            timeout_seconds=args.timeout,
            verify_tls=not args.insecure,
        )
    except requests.HTTPError as http_err:
        status = http_err.response.status_code if http_err.response is not None else '-'
        print(f'HTTP error: {status} - {http_err}', file=sys.stderr)
        return 1
    except requests.RequestException as req_err:
        print(f'Request error: {req_err}', file=sys.stderr)
        return 1
    except ValueError as val_err:
        print(f'Parse error: {val_err}', file=sys.stderr)
        return 1

    print_tenant_buffers(payload)

    in_progress = payload.get('in_progress_batches') or []
    print_batches('In-Progress Batches', in_progress, limit=args.limit)

    recent = payload.get('recent_batches') or []
    print_batches('Recent Batches', recent, limit=args.limit)

    return 0


if __name__ == '__main__':
    load_dotenv()
    raise SystemExit(main())
