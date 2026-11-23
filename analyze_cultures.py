"""Coverage-aware analysis of documented catalog culture labels (revised Q3)."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from process_data import plt

MIN_DOCUMENTED = 20
MIN_COVERAGE = 0.80


def normalize_culture(series):
    # Preserve catalog granularity; normalize only whitespace and explicit missing labels.
    labels = series.astype('string').str.replace(r'\s+', ' ', regex=True).str.strip()
    missing = labels.str.casefold().isin(['', 'unknown', 'unidentified', 'not known', 'not recorded'])
    return labels.mask(missing, pd.NA)


def uncertain_culture(labels):
    # Keep composite/uncertain labels intact; assess exclusion separately.
    return labels.str.contains(r'\bor\b|\bpossibly\b|\bprobably\b|\bperhaps\b|\?|attributed',
                               case=False, regex=True, na=False)


def diversity_from_counts(counts):
    """Vectorized row-wise Shannon entropy and Gini-Simpson index; empty rows are undefined."""
    counts = np.asarray(counts, dtype=float)
    if counts.ndim != 2 or not np.isfinite(counts).all() or (counts < 0).any():
        raise ValueError('Expected a finite, nonnegative two-dimensional count matrix')
    totals = counts.sum(axis=1, keepdims=True)
    probabilities = np.divide(counts, totals, out=np.zeros_like(counts), where=totals > 0)
    # Avoid evaluating log(0); zeros contribute zero to the entropy sum.
    logs = np.log(probabilities, out=np.zeros_like(probabilities), where=probabilities > 0)
    shannon = -(probabilities * logs).sum(axis=1)
    simpson = 1 - np.square(probabilities).sum(axis=1)
    empty = totals.ravel() == 0
    shannon[empty] = np.nan
    simpson[empty] = np.nan
    return {'shannon_nats': shannon, 'gini_simpson': simpson, 'effective_labels': np.exp(shannon)}


def culture_summary(df, by_century=False, exclude_wide=False, exclude_uncertain=False,
                    min_documented=MIN_DOCUMENTED, min_coverage=MIN_COVERAGE):
    if min_documented < 1 or not 0 <= min_coverage <= 1:
        raise ValueError('Invalid count or coverage threshold')
    keys = ['department', 'century'] if by_century else ['department']
    work = df.copy()
    if by_century:
        work = work.loc[work['date_begin_usable'].eq(True) & work['century'].notna()].copy()
        work['century'] = work['century'].astype(int)
    if exclude_wide:
        work = work.loc[~work['date_wide_span'].eq(True)].copy()
    if work.empty:
        return pd.DataFrame(columns=keys + ['records', 'documented', 'coverage', 'sufficient_n']), pd.DataFrame()
    work['culture_label'] = normalize_culture(work['culture'])
    work['uncertain_label'] = uncertain_culture(work['culture_label'])
    if exclude_uncertain:
        work.loc[work['uncertain_label'], 'culture_label'] = pd.NA
    grouped = work.groupby(keys, dropna=False)
    coverage = grouped.agg(records=('objectID', 'size'), documented=('culture_label', 'count'),
                           uncertain_label_records=('uncertain_label', 'sum'))
    coverage['missing'] = coverage['records'] - coverage['documented']
    coverage['coverage'] = coverage['documented'] / coverage['records']
    if work['culture_label'].notna().any():
        counts = pd.crosstab([work[k] for k in keys], work['culture_label']).reindex(coverage.index, fill_value=0)
    else:
        counts = pd.DataFrame(index=coverage.index)
    for name, values in diversity_from_counts(counts.to_numpy(dtype=float)).items():
        coverage[name] = values
    coverage['distinct_labels'] = counts.gt(0).sum(axis=1)
    coverage['sufficient_n'] = coverage['documented'].ge(min_documented) & coverage['coverage'].ge(min_coverage)
    if counts.shape[1]:
        labels = counts.rename_axis(columns='culture_label').stack(future_stack=True).rename('count').reset_index()
        labels = labels.loc[labels['count'].gt(0)].merge(coverage[['documented']].reset_index(), on=keys, validate='many_to_one')
        labels['share_documented'] = labels['count'] / labels['documented']
    else:
        labels = pd.DataFrame(columns=keys + ['culture_label', 'count', 'documented', 'share_documented'])
    return coverage.reset_index(), labels


def compare_treatments(main, sensitivity):
    keys = ['department', 'century']
    renamed = sensitivity.rename(columns={c: c + '_sensitivity' for c in sensitivity.columns if c not in keys})
    merged = main.merge(renamed, on=keys, how='left', validate='one_to_one')
    merged['comparable'] = merged['sufficient_n'] & merged['sufficient_n_sensitivity'].eq(True)
    merged['shannon_change'] = merged['shannon_nats_sensitivity'] - merged['shannon_nats']
    return merged


def century_label(c):
    return f'{abs(int(c))} {"BCE" if c < 0 else "CE"}'


def plot_cultures(departments, centuries, labels, path):
    names = departments['department'].tolist()
    fig, axes = plt.subplots(len(names), 2, figsize=(16, 4.2 * len(names)), squeeze=False)
    for row, name in enumerate(names):
        stats = departments.loc[departments['department'].eq(name)].iloc[0]
        top = labels.loc[labels['department'].eq(name)].sort_values(['count', 'culture_label'], ascending=[False, True]).head(8)
        left, right = axes[row]
        left.set_title(f'{name}: documented {int(stats.documented)}/{int(stats.records)}')
        if top.empty:
            left.text(0.5, 0.5, 'No documented culture labels\nDiversity is undefined, not zero', ha='center', transform=left.transAxes)
            left.set_axis_off()
        else:
            display = top.iloc[::-1]
            left.barh(range(len(display)), display['share_documented'] * 100, color='#3779a8')
            left.set_yticks(range(len(display)), [str(v)[:40] for v in display['culture_label']], fontsize=8)
            left.set_xlabel('Percent of documented labels (top 8; remainder not shown)')
        qualified = centuries.loc[centuries['department'].eq(name) & centuries['sufficient_n']].sort_values('century')
        right.set_title('Shannon entropy by recorded begin-century')
        if qualified.empty:
            right.text(0.5, 0.5, 'No groups pass the count/coverage rules', ha='center', transform=right.transAxes)
            right.set_axis_off()
        else:
            right.scatter(range(len(qualified)), qualified['shannon_nats'], color='#a24b33')
            right.set_xticks(range(len(qualified)), [f'{century_label(c)}\nn={n}' for c, n in zip(qualified.century, qualified.documented)], fontsize=8)
            right.set_ylabel('Shannon entropy (natural-log units)')
            right.set_xlabel('Documented n >= 20; coverage >= 80%; gaps omitted')
            right.grid(axis='y', alpha=0.2)
    fig.suptitle('Recorded culture labels: coverage, concentration, and within-department variation', fontsize=14)
    fig.text(0.02, 0.01, 'Catalog labels retain their original granularity. Missing values excluded from diversity, with coverage reported separately.\n'
             'Indices describe documented sample labels, not population or societal diversity; different departments use different vocabularies.', fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_report(departments, labels, centuries, wide_changes, uncertain_changes, path):
    lines = ['# Q3: Which culture labels are represented, and how concentrated are they?', '',
             '## Revised question and interpretation', '',
             'The proposal mentioned artist nationalities and geographic origins. Coverage checks showed that these fields cannot support a uniform three-department comparison. Q3 therefore describes the actual `culture` catalog labels, retaining compound labels such as `Greek, Attic` and `China or Japan`. These are not interchangeable with countries, artist nationality, or societal diversity.', '',
             'Department summaries use all sampled records, including those without usable dates. Century summaries use only date-eligible records. Missing labels are excluded from index denominators and reported separately. Whitespace is normalized; no geopolitical or ethnic recoding is applied.', '',
             '## Coverage and departmental descriptive statistics', '',
             '| Department | Sample n | Documented n | Coverage | Distinct labels | Shannon H | Gini-Simpson | Effective labels |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in departments.itertuples():
        fmt = lambda value: 'undefined' if pd.isna(value) else f'{value:.3f}'
        lines.append(f'| {r.department} | {r.records} | {r.documented} | {100*r.coverage:.1f}% | {r.distinct_labels} | {fmt(r.shannon_nats)} | {fmt(r.gini_simpson)} | {fmt(r.effective_labels)} |')
    lines += ['', '**Missing does not mean zero diversity.** European Paintings has no documented culture labels in this sample; its indices are undefined. Artist-nationality values are not substituted into this field.', '',
              '## Most frequent documented labels', '',
              '| Department | Catalog label | Records | Share among documented records |',
              '|---|---|---:|---:|']
    for name, group in labels.groupby('department'):
        top = group.sort_values(['count', 'culture_label'], ascending=[False, True]).head(3)
        for r in top.itertuples():
            lines.append(f'| {name} | {r.culture_label.replace("|", "/")} | {r.count} | {100*r.share_documented:.1f}% |')
    lines += ['', '**Descriptive conclusion:** ', '']
    for name, group in labels.groupby('department'):
        top = group.sort_values(['count', 'culture_label'], ascending=[False, True]).head(2)
        label_text = ', '.join(f'{r.culture_label} ({r.count})' for r in top.itertuples())
        total = int(top.documented.iloc[0])
        lines.append(f'- {name}: the two most frequent documented labels are {label_text}; together they account for {100*top["count"].sum()/total:.1f}% of documented records. This is concentration in catalog labeling, not the true distribution of cultures or geographic origins.')
    lines += ['', '## NumPy computation', '', 'For each group, counts are normalized with broadcasting. Shannon H = -sum(p * ln(p)); Gini-Simpson = 1 - sum(p**2); exp(H) is an effective number of equally frequent labels. Zero probabilities contribute zero without evaluating ln(0). An all-missing group returns undefined indices, not H=0. No library diversity helper is used.', '',
              '![Culture label analysis](figures/q3_cultures.png)', '',
              f'Of {len(centuries)} observed date-eligible department-century groups, {int(centuries.sufficient_n.sum())} meet both documented n >= 20 and coverage >= 80%. All groups remain in the CSV; this threshold is a descriptive guardrail, not a guarantee of precision or significance.', '',
              '## Sensitivity and limitations', '']
    for title, changes in [('excluding date spans over 500 years', wide_changes), ('excluding explicitly uncertain attributions', uncertain_changes)]:
        qualified = changes.loc[changes.comparable]
        lines.append(f'- When {title}, {len(qualified)} groups qualify in both treatments.')
        if not qualified.empty:
            row = qualified.loc[qualified.shannon_change.abs().idxmax()]
            lines.append(f'  Largest absolute Shannon change among those groups: {abs(row.shannon_change):.3f} nats ({row.department}, {century_label(row.century)}).')
        lost = changes.loc[changes.sufficient_n & ~changes.comparable]
        for r in lost.itertuples():
            lines.append(f'  Threshold-sensitive group: {r.department}, {century_label(r.century)} no longer qualifies.')
    lines += ['', '- Exact labels have different granularity across departments; an index ranking is not evidence that one historical society was more diverse.',
              '- Observed richness/entropy depend on sample size and catalog practice. Century sample sizes differ; no rarefaction or population-diversity inference is claimed.',
              '- Uncertain attributions are not split into invented multiple records. The sensitivity check excludes labels containing or, possibly, probably, perhaps, ?, or attributed. Commas alone do not imply uncertainty; Greek, Attic remains intact.',
              '- Begin years are interval bounds; excluding extremely wide ranges does not eliminate all dating uncertainty.', '',
              '## Reproduce', '', '```bash', 'python analyze_cultures.py', '```', '',
              'Outputs: department coverage/statistics, full century summaries, documented-label counts, uncertain-label counts, sensitivity tables, a figure, and this report. The committed compact snapshot is sufficient; no fresh API requests are needed.', '']
    path.write_text('\n'.join(line.rstrip() for line in lines), encoding='utf-8')


def analyze(data_path, output_dir):
    df = pd.read_csv(data_path, low_memory=False)
    departments, labels = culture_summary(df)
    centuries, _ = culture_summary(df, by_century=True)
    narrow, _ = culture_summary(df, by_century=True, exclude_wide=True)
    certain, _ = culture_summary(df, by_century=True, exclude_uncertain=True)
    wide_changes = compare_treatments(centuries, narrow)
    uncertain_changes = compare_treatments(centuries, certain)
    results, figures = output_dir / 'results', output_dir / 'figures'
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    for name, table in [('q3_department_summary', departments), ('q3_culture_counts', labels), ('q3_century_summary', centuries),
                        ('q3_excluding_wide_dates', narrow), ('q3_excluding_uncertain_labels', certain),
                        ('q3_wide_date_changes', wide_changes), ('q3_uncertain_label_changes', uncertain_changes)]:
        table.to_csv(results / f'{name}.csv', index=False)
    uncertain = labels.loc[uncertain_culture(labels['culture_label'].astype('string'))]
    uncertain.to_csv(results / 'q3_uncertain_labels.csv', index=False)
    meta = {'sample_records': len(df), 'date_eligible_records': int(df['date_begin_usable'].sum()),
            'documented_culture_records': int(departments.documented.sum()),
            'qualifying_century_groups': int(centuries.sufficient_n.sum()),
            'min_documented': MIN_DOCUMENTED, 'min_coverage': MIN_COVERAGE,
            'scope': 'Documented catalog culture labels, not artist nationality, countries, or population diversity.'}
    (results / 'q3_summary.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    plot_cultures(departments, centuries, labels, figures / 'q3_cultures.png')
    write_report(departments, labels, centuries, wide_changes, uncertain_changes, output_dir / 'q3_results.md')
    print(departments.to_string(index=False))
    print(json.dumps(meta, indent=2))
    return departments, centuries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('app_data/objects.csv'))
    parser.add_argument('--output-dir', type=Path, default=Path('reports'))
    args = parser.parse_args()
    analyze(args.data, args.output_dir)
