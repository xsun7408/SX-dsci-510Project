"""Describe within-department medium composition by recorded start century."""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from process_data import MEDIUM_RULES, MEDIUM_RULE_VERSION
import matplotlib.pyplot as plt


# Preserve every observed group; mark small denominators instead of turning them into zero.
def medium_composition(df, min_count=20, exclude_wide=False):
    if min_count < 1:
        raise ValueError('min_count must be positive')
    eligible = df['date_begin_usable'].eq(True) & df['century'].notna()
    if exclude_wide:
        eligible &= ~df['date_wide_span'].eq(True)
    selected = df.loc[eligible].copy()
    if selected.empty:
        return pd.DataFrame(columns=['department', 'century', 'medium_category', 'count', 'records', 'share', 'sufficient_n'])
    table = pd.crosstab([selected['department'], selected['century']], selected['medium_category'])
    # Keep a fixed category universe, including categories absent after date exclusions.
    table = table.reindex(columns=sorted(df['medium_category'].dropna().unique()), fill_value=0)
    counts = table.to_numpy(dtype=float)
    totals = counts.sum(axis=1, keepdims=True)
    # Broadcasting turns row counts into proportions; unknown/other remain in denominators.
    shares = np.divide(counts, totals, out=np.zeros_like(counts), where=totals > 0)
    count_frame = table.rename_axis(columns='medium_category').stack(future_stack=True).rename('count')
    share_frame = pd.DataFrame(shares, index=table.index, columns=table.columns).rename_axis(columns='medium_category').stack(future_stack=True).rename('share')
    result = pd.concat([count_frame, share_frame], axis=1).reset_index()
    group_totals = table.sum(axis=1).rename('records').reset_index()
    result = result.merge(group_totals, on=['department', 'century'], validate='many_to_one')
    result['century'] = result['century'].astype(int)
    result['sufficient_n'] = result['records'].ge(min_count)
    return result


def century_label(value):
    return f'{abs(int(value))} {"BCE" if value < 0 else "CE"}'


# Compare only groups passing the same sample-size rule in both date treatments.
def sensitivity_changes(main, sensitivity):
    keys = ['department', 'century', 'medium_category']
    stable = sensitivity.rename(columns={c: c + '_excluding_wide' for c in sensitivity.columns if c not in keys})
    joined = main.merge(stable, on=keys, how='inner', validate='one_to_one')
    joined = joined.loc[joined['sufficient_n'] & joined['sufficient_n_excluding_wide']].copy()
    joined['change_percentage_points'] = (joined['share_excluding_wide'] - joined['share']) * 100
    return joined


def plot_composition(composition, destination, min_count):
    departments = sorted(composition['department'].unique())
    fig, axes = plt.subplots(len(departments), 1, figsize=(12, 4.5 * len(departments)), squeeze=False)
    for ax, department in zip(axes.ravel(), departments):
        group = composition.loc[composition['department'].eq(department) & composition['sufficient_n']]
        if group.empty:
            ax.text(0.5, 0.5, f'No centuries with n >= {min_count}', ha='center')
            ax.set_title(department)
            continue
        pivot = group.pivot(index='medium_category', columns='century', values='share').fillna(0)
        pivot = pivot.loc[pivot.sum(axis=1).gt(0)]
        pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
        n = group.groupby('century')['records'].first()
        image = ax.imshow(pivot.to_numpy() * 100, vmin=0, vmax=100, cmap='Blues', aspect='auto')
        ax.set_xticks(range(len(pivot.columns)), [f'{century_label(c)}\nn={int(n.loc[c])}' for c in pivot.columns])
        ax.set_yticks(range(len(pivot)), [c.replace('_', ' ') for c in pivot.index], fontsize=8)
        ax.set_title(department)
        ax.set_xlabel('Recorded begin-year century; observed qualifying centuries only (gaps omitted)')
        for row, values in enumerate(pivot.to_numpy()):
            for col, value in enumerate(values):
                if value >= 0.1:
                    ax.text(col, row, f'{100 * value:.0f}', ha='center', va='center', fontsize=8,
                            color='white' if value >= 0.55 else 'black')
        fig.colorbar(image, ax=ax, label='Within-department/century percent', fraction=0.025)
    fig.suptitle(f'Medium composition of sampled metadata (century n >= {min_count})', fontsize=14)
    fig.text(0.02, 0.012, 'Ordered coarse keyword categories; other/unknown retained. Begin years are date bounds. '
             'Not a collection-wide history of material use.', fontsize=8)
    fig.tight_layout(rect=(0, 0.035, 1, 0.97))
    fig.savefig(destination, dpi=160)
    plt.close(fig)


# Earliest/latest qualifiers are chosen by sample-size rule, not by which percentages look interesting.
def write_report(main, changes, coverage, metadata, path, min_count):
    lines = ['# Q2: How does medium composition vary across recorded centuries?', '',
             '## Population and method', '',
             f"The analysis uses {metadata['date_eligible_records']:,} date-eligible records from the fixed 3,000-object sample. "
             f"Each department-century is normalized separately with NumPy broadcasting. All observed groups are saved; "
             f"the main figure and endpoint contrasts require n >= {min_count}. Unknown and other categories remain in the denominator.", '',
             '![Medium composition by century](figures/q2_medium_composition.png)', '',
             '## Earliest and latest qualifying centuries', '',
             'These endpoints describe the observed sample and can be far apart. They do not establish a continuous historical trend.', '',
             '| Department | Century | Records | Most frequent category | Count | Share |',
             '|---|---|---:|---|---:|---:|']
    for department, group in main.loc[main['sufficient_n']].groupby('department'):
        for century in sorted({group['century'].min(), group['century'].max()}):
            row = group.loc[group['century'].eq(century)].sort_values(['count', 'medium_category'], ascending=[False, True]).iloc[0]
            lines.append(f"| {department} | {century_label(century)} | {int(row['records'])} | {row['medium_category']} | {int(row['count'])} | {100 * row['share']:.1f}% |")
    european = main.loc[main['department'].eq('European Paintings') & main['sufficient_n']]
    if not european.empty:
        early = european.loc[european['century'].eq(european['century'].min())].sort_values('count', ascending=False).iloc[0]
        late = european.loc[european['century'].eq(european['century'].max())].sort_values('count', ascending=False).iloc[0]
        lines += ['', '**Descriptive finding:** In sampled European Paintings records, the most frequent category changes '
                  f"from {early['medium_category']} ({int(early['count'])}/{int(early['records'])}, {100*early['share']:.1f}%) "
                  f"in recorded begin-century {century_label(early['century'])} to {late['medium_category']} "
                  f"({int(late['count'])}/{int(late['records'])}, {100*late['share']:.1f}%) in {century_label(late['century'])}. "
                  'This supports a difference in sampled catalog composition, not a causal or collection-wide account of artistic evolution.']
    lines += ['', '## Sensitivity and limitations', '',
              f"Excluding intervals wider than 500 years leaves {metadata['date_eligible_excluding_wide']:,} date-eligible records. "
              'Comparisons below include only department-centuries with sufficient sample sizes in both treatments. ']
    lost = coverage.loc[coverage['sufficient_n'] & ~coverage['sufficient_n_excluding_wide']]
    for row in lost.itertuples():
        lines.append(f'- Threshold-sensitive group: {row.department}, {century_label(row.century)} falls from n={row.records} to n={row.records_excluding_wide} after wide-date exclusion; its endpoint or apparent prominence should not be treated as a stable century-specific finding.')
    for department, group in changes.groupby('department'):
        row = group.loc[group['change_percentage_points'].abs().idxmax()]
        lines.append(f"- {department}: largest absolute category change is {abs(row['change_percentage_points']):.1f} percentage points "
                     f"({row['medium_category']}, {century_label(row['century'])}: {100*row['share']:.1f}% to {100*row['share_excluding_wide']:.1f}%).")
    lines += ['', '- Department sample sizes are fixed by design; pooled counts cannot describe the museum\'s actual department proportions.',
              '- These are descriptive comparisons of catalog date lower bounds; century assignment can be uncertain for wide or cross-century intervals. This check does not resolve every date uncertainty.',
              '- The n >= 20 rule limits sparse comparisons, but does not guarantee precision or statistical significance. Small groups remain in the CSV.',
              '- Medium categories mix technique and material using a documented priority. Composite media may fit multiple patterns; a first match is an analytic convention, not a definitive catalog classification.',
              '- Missing or unmatched medium text is retained. A high percentage within a century does not imply worldwide artistic dominance.', '',
              '## Reproduce', '', '```bash',
              'python process_data.py data/sample_3000_510.json --output-dir data/processed_3000',
              'python analyze_media.py --data data/processed_3000/objects_clean.csv --output-dir reports',
              '```', '', 'Outputs include full counts/proportions, a wide-date sensitivity table, medium-rule audit, figure, and this report.', '']
    path.write_text('\n'.join(line.rstrip() for line in lines), encoding='utf-8')


def analyze(data_path, output_dir, min_count=20):
    df = pd.read_csv(data_path, low_memory=False)
    main = medium_composition(df, min_count)
    if main.empty:
        raise ValueError('No eligible dates for Q2')
    sensitivity = medium_composition(df, min_count, exclude_wide=True)
    changes = sensitivity_changes(main, sensitivity)
    results, figures = output_dir / 'results', output_dir / 'figures'
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    main.to_csv(results / 'q2_medium_by_century.csv', index=False)
    sensitivity.to_csv(results / 'q2_excluding_wide_dates.csv', index=False)
    changes.to_csv(results / 'q2_sensitivity_changes.csv', index=False)
    coverage = main.groupby(['department', 'century'])[['records', 'sufficient_n']].first()
    narrow_n = sensitivity.groupby(['department', 'century'])['records'].first()
    coverage['records_excluding_wide'] = narrow_n.reindex(coverage.index, fill_value=0).astype(int)
    coverage['sufficient_n_excluding_wide'] = coverage['records_excluding_wide'].ge(min_count)
    coverage = coverage.reset_index()
    coverage.to_csv(results / 'q2_group_coverage.csv', index=False)
    # Audit all distinct strings and rule overlaps without uploading complete object responses.
    medium = df[['department', 'medium', 'medium_category']].copy()
    medium['medium'] = medium['medium'].fillna('[not recorded]')
    medium = medium.groupby(['department', 'medium', 'medium_category']).size().rename('records').reset_index()
    medium['matched_categories'] = medium['medium'].map(lambda text: '|'.join(label for label, pattern in MEDIUM_RULES
                                                                            if re.search(pattern, text, flags=re.IGNORECASE)))
    medium.to_csv(results / 'q2_medium_rule_audit.csv', index=False)
    metadata = {'medium_rule_version': MEDIUM_RULE_VERSION, 'sample_records': len(df),
                'date_eligible_records': int(df['date_begin_usable'].sum()),
                'date_eligible_excluding_wide': int((df['date_begin_usable'] & ~df['date_wide_span']).sum()),
                'min_century_records': min_count, 'observed_department_centuries': int(main[['department', 'century']].drop_duplicates().shape[0]),
                'qualifying_department_centuries': int(main.loc[main['sufficient_n'], ['department', 'century']].drop_duplicates().shape[0]),
                'unclassified_or_missing_records': int(df['medium_category'].isin(['other', 'unknown']).sum()),
                'note': 'All observed groups retained. Main figure/endpoints use the minimum-size rule. Descriptive sample composition only.'}
    (results / 'q2_summary.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    plot_composition(main, figures / 'q2_medium_composition.png', min_count)
    write_report(main, changes, coverage, metadata, output_dir / 'q2_results.md', min_count)
    print(json.dumps(metadata, indent=2))
    return main, sensitivity


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data/processed_3000/objects_clean.csv'))
    parser.add_argument('--output-dir', type=Path, default=Path('reports'))
    parser.add_argument('--min-count', type=int, default=20)
    args = parser.parse_args()
    analyze(args.data, args.output_dir, args.min_count)
