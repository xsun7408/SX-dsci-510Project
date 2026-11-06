"""Export a compact processed snapshot for hosting without raw API responses."""
import argparse
import json
from pathlib import Path

import pandas as pd

from process_data import MEDIUM_RULE_VERSION

COLUMNS = ['objectID', 'title', 'department', 'objectDate', 'medium', 'culture',
           'artistDisplayName', 'artistNationality', 'begin_year', 'end_year',
           'century', 'medium_category', 'date_begin_usable', 'date_wide_span']


def export(data, manifest_path, destination):
    df = pd.read_csv(data, low_memory=False)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if df['objectID'].duplicated().any() or set(df['objectID']) != set(manifest['objectIDs']):
        raise ValueError('Processed data must match the fixed manifest exactly')
    destination.mkdir(parents=True, exist_ok=True)
    df[COLUMNS].to_csv(destination / 'objects.csv', index=False)
    metadata = {'records': len(df), 'date_eligible_records': int(df['date_begin_usable'].sum()),
                'medium_rule_version': MEDIUM_RULE_VERSION, 'manifest': manifest_path.name,
                'description': 'Compact processed metadata snapshot; no raw JSON responses, images, logs, or secrets.'}
    (destination / 'snapshot.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data/processed_3000/objects_clean.csv'))
    parser.add_argument('--manifest', type=Path, default=Path('sampling/sample_3000_510.json'))
    parser.add_argument('--output-dir', type=Path, default=Path('app_data'))
    args = parser.parse_args()
    export(args.data, args.manifest, args.output_dir)
