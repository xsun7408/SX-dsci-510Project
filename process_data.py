"""Clean a manifest-selected Met sample and answer the first temporal question."""

import argparse
import json
import os
from pathlib import Path


import numpy as np
import pandas as pd


# Keep plotting caches writable on cloud machines with read-only home directories.
os.environ.setdefault('MPLCONFIGDIR', '/tmp/dsci510-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME', '/tmp/dsci510-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from acquire import load_cache


# First matching category wins; preserve the raw medium for review.
MEDIUM_RULES = [
    ('oil_painting', r'\boil\b'),
    ('tempera_painting', r'\btempera\b'),
    ('ceramic', r'ceramic|porcelain|terracotta|terra\s*cotta|stoneware|earthenware|pottery|faience'),
    ('textile', r'textile|silk|cotton|wool|linen|tapestry|embroid|weav|woven|velvet'),
    ('bronze', r'\bbronze\b'),
    ('glass', r'\bglass\b'),
    ('ink_watercolor_print', r'\bink\b|watercolor|watercolour|woodblock|engraving|etching|lithograph'),
    ('stone', r'marble|limestone|sandstone|granite|jade|\bstone\b|alabaster'),
    ('other_metal', r'\bgold\b|\bsilver\b|\bcopper\b|\biron\b|\blead\b|\bmetal\b'),
    ('wood', r'\bwood\b|bamboo'),
]


# Signed centuries: -100..-1 -> -1, 1..100 -> 1; leave zero/malformed years unset.
def centuries(years):
    values = pd.to_numeric(years, errors='coerce').to_numpy(dtype=float, na_value=np.nan)
    valid = np.isfinite(values) & (values != 0) & (values == np.trunc(values))
    result = np.full(len(values), np.nan)
    result[valid] = np.sign(values[valid]) * np.ceil(np.abs(values[valid]) / 100)
    return pd.Series(result, index=years.index, dtype='Int64')


# Assign coarse, mutually exclusive categories using ordered keyword rules.
def classify_medium(series):
    text = series.astype('string')
    result = pd.Series('other', index=series.index, dtype='string')
    unmatched = text.notna()
    result.loc[~unmatched] = 'unknown'
    for label, pattern in MEDIUM_RULES:
        hit = unmatched & text.str.contains(pattern, case=False, regex=True, na=False)
        result.loc[hit] = label
        unmatched &= ~hit
    return result


# Preserve records and raw date fields; add flags and analysis features.
def build_dataframe(records):
    if not records:
        raise ValueError('No records to process')
    df = pd.DataFrame(records).replace(r'^\s*$', pd.NA, regex=True)
    for column in ['objectID', 'department', 'medium', 'objectDate', 'objectBeginDate', 'objectEndDate']:
        if column not in df:
            df[column] = pd.NA
    if df['objectID'].isna().any() or df['objectID'].duplicated().any():
        raise ValueError('Missing or duplicate objectID')
    begin = pd.to_numeric(df['objectBeginDate'], errors='coerce')
    end = pd.to_numeric(df['objectEndDate'], errors='coerce')
    df['begin_year'] = begin
    df['end_year'] = end
    df['date_span_years'] = end - begin

    # Zero bounds require review; 0/0 with no date description is likely unknown.
    df['date_unknown'] = begin.eq(0) & end.eq(0) & df['objectDate'].isna()
    df['date_zero_review'] = (begin.eq(0) | end.eq(0)) & ~df['date_unknown']
    df['date_missing_numeric'] = begin.isna() | end.isna()
    df['date_reversed'] = begin.gt(end)
    df['date_wide_span'] = df['date_span_years'].gt(500)

    # Q1 excludes missing, nonfinite, noninteger, reversed, and zero-bound intervals.
    df['date_begin_usable'] = (
        ~df['date_missing_numeric'] & ~df['date_reversed']
        & begin.ne(0) & end.ne(0)
        & np.isfinite(begin) & np.isfinite(end)
        & begin.eq(np.trunc(begin)) & end.eq(np.trunc(end))
    ).fillna(False).astype(bool)

    # Century uses the recorded interval start, not an exact creation date.
    df['century'] = centuries(begin.where(df['date_begin_usable']))
    df['century_label'] = df['century'].map(
        lambda c: pd.NA if pd.isna(c) else f'{abs(int(c))} century {"BCE" if c < 0 else "CE"}'
    ).astype('string')
    df['medium_category'] = classify_medium(df['medium'])
    return df


# NumPy summaries use valid start years, with an optional wide-interval exclusion.
def temporal_summary(df, exclude_wide=False):
    eligible = df['date_begin_usable']
    if exclude_wide:
        eligible = eligible & ~df['date_wide_span']
    rows = []
    for department, group in df.groupby('department', dropna=False):
        years = group.loc[eligible.loc[group.index], 'begin_year'].to_numpy(dtype=float)
        if len(years):
            q1, q3 = np.percentile(years, [25, 75])
            median = float(np.median(years))
        else:
            q1 = q3 = median = np.nan
        rows.append({'department': department, 'sample_records': len(group), 'valid_date_records': len(years),
                     'median_begin_year': median, 'q1_begin_year': q1, 'q3_begin_year': q3, 'iqr_years': q3 - q1})
    return pd.DataFrame(rows)


def process(manifest_path, output_dir):
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    ids = manifest['objectIDs']
    if len(ids) != len(set(ids)) or len(ids) != manifest['target']:
        raise ValueError('Manifest contains duplicate IDs or a target/count mismatch')
    cached = load_cache(manifest_path.parent / 'objects.jsonl')
    missing = [i for i in ids if i not in cached]
    # Never publish a partial acquisition as a complete-sample analysis.
    if missing:
        raise ValueError(f'{len(missing)} sampled IDs still missing; finish acquisition first')
    df = build_dataframe([cached[i] for i in ids])
    output_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_dir / 'objects_clean.csv', index=False)
    summary = temporal_summary(df)
    summary.to_csv(output_dir / 'q1_temporal_summary.csv', index=False)

    # Check whether temporal conclusions depend on intervals wider than 500 years.
    sensitivity = temporal_summary(df, exclude_wide=True)
    sensitivity.to_csv(output_dir / 'q1_excluding_wide_dates.csv', index=False)
    review = df.loc[~df['date_begin_usable'] | df['date_wide_span'],
                    ['objectID', 'department', 'title', 'objectDate', 'begin_year', 'end_year',
                     'date_unknown', 'date_zero_review', 'date_reversed', 'date_wide_span']]
    review.to_csv(output_dir / 'date_review.csv', index=False)
    df.groupby(['department', 'medium_category']).size().rename('count').to_csv(output_dir / 'medium_counts.csv')
    df.loc[df['medium_category'].isin(['other', 'unknown']),
           ['objectID', 'department', 'medium', 'medium_category']].to_csv(output_dir / 'medium_review.csv', index=False)

    # Plot the observed sample; keep uncertain/wide-date limitations explicit.
    groups = [(str(name), g.loc[g['date_begin_usable'], 'begin_year'].to_numpy(dtype=float))
              for name, g in df.groupby('department')]
    groups = [(name, values) for name, values in groups if len(values)]
    if not groups:
        raise ValueError('No valid dates to plot')
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.boxplot([values for _, values in groups], orientation='horizontal', tick_labels=[name for name, _ in groups])
    ax.set_xlabel('Recorded begin year (negative = BCE; positive = CE)')
    ax.set_title(f'Sampled object date ranges: begin-year distributions (n={len(df)})')
    ax.grid(axis='x', alpha=0.25)
    fig.text(0.02, 0.02, 'Equal department targets; known nonzero date bounds only. Box = Q1–Q3; line = median.\n'
             'Whiskers use 1.5 IQR. Start dates are interval bounds; wide ranges retained in this figure.', fontsize=8)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(output_dir / 'q1_date_distribution.png', dpi=160)
    plt.close(fig)

    metadata = {'manifest': manifest_path.name, 'sample_records': len(df),
                'valid_date_records': int(df['date_begin_usable'].sum()),
                'unknown_dates': int(df['date_unknown'].sum()), 'zero_date_review': int(df['date_zero_review'].sum()),
                'wide_date_spans': int(df['date_wide_span'].sum()),
                'medium_other_or_unknown': int(df['medium_category'].isin(['other', 'unknown']).sum()),
                'date_rule': 'Begin-year analysis; exclude missing/nonfinite/noninteger/reversed/zero-bound intervals; wide spans retained with separate sensitivity results.',
                'scope': 'Equal-target department sample of metadata, not collection proportions; no isPublicDomain filter.'}
    (output_dir / 'processing_summary.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(summary.to_string(index=False))
    print(json.dumps(metadata, indent=2))
    return df, summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    process(args.manifest, args.output_dir)
