"""Explore the processed Met sample with a small Streamlit interface."""
from pathlib import Path
import os

import numpy as np
import pandas as pd
import streamlit as st

from process_data import temporal_summary
from analyze_media import medium_composition
from analyze_cultures import culture_summary

ROOT = Path(__file__).resolve().parent
LOCAL_DATA = ROOT / 'data/processed_3000/objects_clean.csv'
DEFAULT_DATA = LOCAL_DATA if LOCAL_DATA.exists() else ROOT / 'app_data/objects.csv'
DATA_PATH = Path(os.environ.get('MET_DATA_PATH', str(DEFAULT_DATA)))


@st.cache_data
# Include the modification time in the key so rerunning processing refreshes the app.
def load_data(path, modified_ns):
    return pd.read_csv(path, low_memory=False)


def main():
    st.set_page_config(page_title='Met Collection Explorer', layout='wide')
    st.title('Met Collection Explorer')
    st.write('Explore recorded dates and materials in a three-department metadata sample.')
    st.caption('Years are recorded interval starts: negative = BCE, positive = CE. Equal department targets do not describe whole-collection proportions.')
    if not DATA_PATH.exists():
        st.error('Processed sample not found. Follow the README to acquire and process the sample before opening the explorer.')
        st.stop()
    df = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
    departments = sorted(df['department'].dropna().unique())
    selected = st.sidebar.selectbox('Department', ['All departments', *departments])
    base = df if selected == 'All departments' else df.loc[df['department'].eq(selected)]
    dated = base.loc[base['date_begin_usable'].eq(True)].copy()
    if dated.empty:
        st.info('No records with eligible dates in this department.')
        st.stop()
    # Keep a common slider domain so department changes preserve the requested range.
    all_dated = df.loc[df['date_begin_usable'].eq(True), 'begin_year']
    minimum, maximum = int(all_dated.min()), int(all_dated.max())
    bounds = st.sidebar.slider('Recorded begin-year range', minimum, maximum, (minimum, maximum))
    filtered = dated.loc[dated['begin_year'].between(*bounds)].copy()
    st.sidebar.caption('Records with zero, missing, or invalid date bounds are excluded from this view. Wide intervals remain included.')
    st.caption(f'Date-eligible records in selected department(s): {len(dated):,} of {len(base):,}. All views below use the same department and year filters.')
    st.metric('Matching records', f'{len(filtered):,}')
    if filtered.empty:
        st.info('No records match these filters. Widen the year range or choose another department.')
        st.stop()
    years = filtered['begin_year'].to_numpy(dtype=float)
    q1, q3 = np.percentile(years, [25, 75])
    left, right = st.columns(2)
    left.metric('Median recorded begin year', f'{np.median(years):g}')
    right.metric('Interquartile range (years)', f'{q3 - q1:g}')

    st.subheader('Recorded begin-year distribution')
    # Bin the filtered years; histogram heights and labels come from processed data.
    counts, edges = np.histogram(years, bins=min(30, max(1, len(np.unique(years)))))
    histogram = pd.DataFrame({'Year-bin start': edges[:-1], 'Records': counts})
    st.bar_chart(histogram, x='Year-bin start', y='Records')
    st.subheader('Department summaries')
    st.dataframe(temporal_summary(filtered), hide_index=True)

    st.subheader('Medium composition by recorded start century')
    st.caption('Ordered coarse categories; other/unknown remain in denominators. Observed centuries can have gaps; these sample proportions do not establish worldwide historical trends.')
    large_groups_only = st.checkbox('Limit medium comparisons to department-centuries with at least 20 records', value=True)
    composition = medium_composition(filtered, min_count=20)
    shown = composition.loc[composition['sufficient_n']] if large_groups_only else composition
    if shown.empty:
        st.info('No department-century has 20 matching records. Widen the date range or turn off the medium sample-size limit.')
    else:
        shares = shown.pivot(index=['department', 'century'], columns='medium_category', values='share') * 100
        counts = shown.groupby(['department', 'century'])['records'].first()
        for department in sorted(shown['department'].unique()):
            trend = shares.loc[department].copy()
            trend.index = [f'{abs(int(c))} {"BCE" if c < 0 else "CE"} (n={int(counts.loc[(department, c)])})' for c in trend.index]
            st.write(department)
            st.bar_chart(trend)
        details = shares.round(1).reset_index()
        details['Records'] = counts.to_numpy()
        st.dataframe(details, hide_index=True)
        if not large_groups_only:
            st.warning('Small century groups are included; large percentages may reflect only one or a few objects.')

    st.subheader('Documented culture labels (Q3)')
    st.caption('This view uses the same date and department filters. Culture, country, and artist nationality are distinct fields. Indices describe recorded labels; differing catalog vocabularies limit cross-department comparisons.')
    culture_coverage, culture_labels = culture_summary(filtered)
    st.dataframe(culture_coverage[['department', 'records', 'documented', 'coverage', 'distinct_labels',
                                   'shannon_nats', 'gini_simpson', 'effective_labels']], hide_index=True)
    if culture_labels.empty:
        st.info('No culture labels are documented in these records. Diversity is undefined, not zero; artist nationality is not substituted.')
    else:
        for department, group in culture_labels.groupby('department'):
            st.write(f'{department}: most frequent documented labels')
            top = group.sort_values(['count', 'culture_label'], ascending=[False, True]).head(8)
            st.bar_chart(top.set_index('culture_label')['share_documented'] * 100)
        culture_centuries, _ = culture_summary(filtered, by_century=True)
        qualified = culture_centuries.loc[culture_centuries['sufficient_n']]
        if qualified.empty:
            st.info('No culture-century groups meet documented n >= 20 and coverage >= 80%. All groups remain in the coverage table.')
        else:
            st.write('Qualified century-level diversity (documented n >= 20; coverage >= 80%)')
            st.dataframe(qualified[['department', 'century', 'records', 'documented', 'coverage',
                                    'shannon_nats', 'gini_simpson']], hide_index=True)
        with st.expander('All century groups, including missing and sparse labels'):
            st.dataframe(culture_centuries, hide_index=True)

    st.subheader('Example object metadata')
    st.caption('Up to five matching objects, sorted by objectID; these are examples, not a representative subsample.')
    fields = ['objectID', 'title', 'department', 'objectDate', 'medium', 'culture', 'artistDisplayName']
    examples = filtered.sort_values('objectID').head(5)
    st.dataframe(examples[fields].fillna('Not recorded'), hide_index=True)
    st.caption(f'Wide date intervals over 500 years among matching records: {int(filtered["date_wide_span"].sum()):,}. See the report for sensitivity analysis.')


if __name__ == '__main__':
    main()
