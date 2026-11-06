"""Acquire a reproducible, department-stratified Met metadata sample."""
import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import random
import time

import requests

BASE_URL = 'https://collectionapi.metmuseum.org/public/collection/v1'
DEFAULT_DEPARTMENTS = [11, 6, 13]  # European Paintings, Asian Art, Greek and Roman Art


class MetClient:
    def __init__(self, interval=1.0, attempts=4):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'DSCI510-MetResearch/0.1 (educational metadata project)'
        self.interval = interval
        self.attempts = attempts
        self.last_request = 0.0

    def get(self, path, params=None):
        for attempt in range(self.attempts):
            time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                response = self.session.get(BASE_URL + path, params=params, timeout=(10, 30))
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict):
                    raise ValueError('Expected a JSON object')
                return result
            except requests.RequestException as exc:
                status = exc.response.status_code if exc.response is not None else None
                retryable = status is None or status == 429 or status in (500, 502, 503, 504)
                if not retryable or attempt + 1 == self.attempts:
                    raise
                delay = 2 ** attempt
                if exc.response is not None:
                    header = exc.response.headers.get('Retry-After', '')
                    if header.isdigit():
                        delay = max(delay, int(header))
                logging.warning('Request failed (%s); retry in %ss', status, delay)
                time.sleep(delay)


def get_departments(client):
    return client.get('/departments')['departments']


def get_object_ids(client, department_id):
    return client.get('/objects', {'departmentIds': department_id}).get('objectIDs') or []


def fetch_object(client, object_id):
    record = client.get(f'/objects/{object_id}')
    if record.get('objectID') != object_id:
        raise ValueError(f'Unexpected objectID for {object_id}')
    return record


def load_cache(path):
    records = {}
    if path.exists():
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                records[record['objectID']] = record
            except (ValueError, KeyError) as exc:
                raise ValueError(f'Invalid cache line {number}; preserve and repair before resuming') from exc
    return records


def iter_records(client, ids, cache_path):
    """Yield cached or fetched records; persist each success before continuing."""
    cached = load_cache(cache_path)
    consecutive_forbidden = 0
    with cache_path.open('a', encoding='utf-8') as output:
        for object_id in ids:
            if object_id in cached:
                yield cached[object_id]
                continue
            try:
                record = fetch_object(client, object_id)
            except (requests.RequestException, ValueError) as exc:
                logging.error('Failed objectID=%s: %s', object_id, exc)
                status = exc.response.status_code if isinstance(exc, requests.RequestException) and exc.response is not None else None
                consecutive_forbidden = consecutive_forbidden + 1 if status == 403 else 0
                if consecutive_forbidden >= 3:
                    logging.error('Stopping after 3 consecutive HTTP 403 responses; preserve cache and resume after investigating access or rate limits')
                    break
                continue
            consecutive_forbidden = 0
            output.write(json.dumps(record, ensure_ascii=False) + '\n')
            output.flush()
            cached[object_id] = record
            yield record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=20, help='Total target, not per department')
    parser.add_argument('--seed', type=int, default=510)
    parser.add_argument('--interval', type=float, default=1.0, help='Minimum seconds between request starts (default: 1)')
    parser.add_argument('--departments', nargs='+', type=int, default=DEFAULT_DEPARTMENTS)
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    args = parser.parse_args()
    if args.count < 1 or len(set(args.departments)) != len(args.departments) or args.interval < 0:
        parser.error('Count must be positive, interval nonnegative, and department IDs unique')
    args.data_dir.mkdir(parents=True, exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(), logging.FileHandler('logs/acquire.log')], format='%(asctime)s %(levelname)s %(message)s')
    client = MetClient(interval=args.interval)
    manifest_path = args.data_dir / f'sample_{args.count}_{args.seed}.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest['departments'] != args.departments or manifest['target'] != args.count or manifest['seed'] != args.seed:
            parser.error('Existing manifest settings differ; use another data directory')
    else:
        departments = get_departments(client)
        valid = {d['departmentId'] for d in departments}
        if not set(args.departments) <= valid:
            parser.error('Unknown department ID')
        rng = random.Random(args.seed)
        selected = []
        for index, department in enumerate(args.departments):
            ids = sorted(set(get_object_ids(client, department)))
            count = args.count // len(args.departments) + (index < args.count % len(args.departments))
            if len(ids) < count:
                parser.error(f'Department {department} has fewer than {count} candidates')
            selected.extend(rng.sample(ids, count))
        manifest = {'target': args.count, 'seed': args.seed, 'departments': args.departments, 'objectIDs': selected, 'acquired_at_utc': datetime.now(timezone.utc).isoformat(), 'base_url': BASE_URL, 'department_catalog': departments}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    records = []
    for record in iter_records(client, manifest['objectIDs'], args.data_dir / 'objects.jsonl'):
        records.append(record)
        if len(records) % 25 == 0:
            logging.info('Progress: %s/%s records available', len(records), args.count)
    failed = sorted(set(manifest['objectIDs']) - {r['objectID'] for r in records})
    summary = {'target': args.count, 'successful': len(records), 'failed_ids': failed, 'missing_ids': failed, 'note': 'Missing IDs include failed and not-yet-attempted requests if acquisition stopped early.', 'completed_at_utc': datetime.now(timezone.utc).isoformat()}
    manifest_path.with_suffix('.result.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    logging.info('Target=%s successful=%s failed=%s', args.count, len(records), len(failed))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
