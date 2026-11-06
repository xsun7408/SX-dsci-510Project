"""Display cached real-data evidence for a short classroom demonstration."""
import argparse
import json
from pathlib import Path

import pandas as pd

from acquire import load_cache
from process_data import build_dataframe, temporal_summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('data/sample_3000_510.json'))
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    cached = load_cache(args.manifest.parent / 'objects.jsonl')
    missing = [i for i in manifest['objectIDs'] if i not in cached]
    if missing:
        raise ValueError(f'{len(missing)} sampled records missing; finish acquisition first')
    # Select the manifest population, not every record in the shared cache.
    records = [cached[i] for i in manifest['objectIDs']]
    raw = pd.DataFrame(records)
    df = build_dataframe(records)
    examples = df.groupby('department').head(1).index
    print('\n1. RAW API RECORDS AS A PANDAS DATAFRAME')
    print('Shape:', raw.shape)
    print(raw.loc[examples, ['department', 'objectBeginDate', 'objectEndDate', 'medium']].to_string(index=False, max_colwidth=28))
    print('\n2. CLEANED FEATURES FROM THE SAME RECORDS')
    print(df.loc[examples, ['department', 'begin_year', 'century', 'medium_category']].to_string(index=False))
    print('Total sampled records:', len(df))
    print('Eligible for Q1:', int(df['date_begin_usable'].sum()))
    print('\n3. PANDAS: ELIGIBLE RECORDS BY DEPARTMENT')
    print(df.groupby('department')['date_begin_usable'].agg(['size', 'sum']).rename(columns={'size': 'sample_records', 'sum': 'eligible_date_records'}).to_string())
    print('\n4. NUMPY: MEDIANS, QUARTILES, AND IQR FROM RECORDED BEGIN YEARS')
    print(temporal_summary(df).to_string(index=False))
    print('\nCached-data demonstration only: no live API calls were made.')


if __name__ == '__main__':
    main()
