"""Explore the processed Met sample with a small Streamlit interface."""
from pathlib import Path
import os

import numpy as np
import pandas as pd
import streamlit as st

from process_data import temporal_summary

ROOT = Path(__file__).resolve().parent
DATA_PATH = Path(os.environ.get('MET_DATA_PATH', str(ROOT / 'data/processed_3000/objects_clean.csv')))


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
    st.caption('Exploratory keyword categories; other/unknown are retained. Centuries with few records can produce unstable percentages.')
    # Preserve department groups, then normalize each observed department-century row.
    table = pd.crosstab([filtered['department'], filtered['century']], filtered['medium_category'])
    matrix = table.to_numpy(dtype=float)
    totals = matrix.sum(axis=1, keepdims=True)
    shares = np.divide(matrix, totals, out=np.zeros_like(matrix), where=totals > 0)
    composition = pd.DataFrame(shares * 100, index=table.index, columns=table.columns)
    options = sorted(int(value) for value in filtered['century'].dropna().unique())
    # A single century has a well-defined composition even when a time trend cannot be inferred.
    century = st.selectbox('Inspect century', options, format_func=lambda c: f'{abs(c)} century {"BCE" if c < 0 else "CE"}')
    century_rows = composition.loc[composition.index.get_level_values('century') == century]
    st.bar_chart(century_rows.droplevel('century'))
    details = composition.round(1).reset_index()
    details['Records'] = totals.ravel().astype(int)
    st.dataframe(details, hide_index=True)

    st.subheader('Example object metadata')
    st.caption('Up to five matching objects, sorted by objectID; these are examples, not a representative subsample.')
    fields = ['objectID', 'title', 'department', 'objectDate', 'medium', 'culture', 'artistDisplayName']
    examples = filtered.sort_values('objectID').head(5)
    st.dataframe(examples[fields].fillna('Not recorded'), hide_index=True)
    st.caption(f'Wide date intervals over 500 years among matching records: {int(filtered["date_wide_span"].sum()):,}. See the report for sensitivity analysis.')


if __name__ == '__main__':
    main()
