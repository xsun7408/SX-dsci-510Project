"""Explore the processed Met sample with a small Streamlit interface."""
from pathlib import Path
import os

import numpy as np
import pandas as pd
import streamlit as st

from process_data import temporal_summary
from analyze_media import medium_composition
from analyze_cultures import culture_summary
from interactive_demo import show_live_demo

ROOT = Path(__file__).resolve().parent
LOCAL_DATA = ROOT / 'data/processed_3000/objects_clean.csv'
DEFAULT_DATA = LOCAL_DATA if LOCAL_DATA.exists() else ROOT / 'app_data/objects.csv'
DATA_PATH = Path(os.environ.get('MET_DATA_PATH', str(DEFAULT_DATA)))


@st.cache_data
# Include the modification time in the key so rerunning processing refreshes the app.
def load_data(path, modified_ns):
    return pd.read_csv(path, low_memory=False)


def show_dates(filtered):
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



def show_media(filtered):
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



def show_cultures(filtered):
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



def show_objects(filtered):
    st.subheader('Object browser')
    st.caption('Search applies only to the object browser, not the Q1/Q2/Q3 analyses. Examples are not a representative random sample.')
    query = st.text_input('Search titles or artists', key='object_search').strip()
    matches = filtered
    if query:
        titles = filtered['title'].astype('string').str.contains(query, case=False, regex=False, na=False)
        artists = filtered['artistDisplayName'].astype('string').str.contains(query, case=False, regex=False, na=False)
        matches = filtered.loc[titles | artists]
    if matches.empty:
        st.info('No objects match this search within the current filters.')
        return
    matches = matches.sort_values('objectID')
    fields = ['objectID', 'title', 'department', 'objectDate', 'medium', 'culture', 'artistDisplayName']
    st.dataframe(matches.head(5)[fields].fillna('Not recorded'), hide_index=True)
    candidates = matches.head(100).set_index('objectID')
    st.caption(f'{len(matches):,} matching objects. The selector offers the first 100 by ID; search to narrow the list.')
    object_id = st.selectbox('Choose an object', candidates.index.tolist(),
                             format_func=lambda value: f'{value} — {candidates.loc[value, "title"]}', key='object_choice')
    detail = candidates.loc[object_id]
    st.subheader(str(detail['title']))
    st.json({'objectID': int(object_id), **{field: None if pd.isna(detail[field]) else str(detail[field]) for field in fields if field != 'objectID'}})
    st.caption(f'Wide date intervals over 500 years among the analytic selection: {int(filtered["date_wide_span"].sum()):,}.')


def set_filters(department, bounds):
    st.session_state['department_filter'] = department
    st.session_state['year_filter'] = bounds
    st.session_state['medium_filter'] = 'All medium groups'


def main():
    st.set_page_config(page_title='Met Collection Explorer', layout='wide')
    st.title('Met Collection Explorer')
    st.write('Ask a question, change the filters, and inspect the evidence in a real museum sample.')
    st.caption('Recorded begin years are date-range bounds: negative = BCE, positive = CE. The department sample targets are equal by design.')
    if not DATA_PATH.exists():
        st.error('Processed sample not found. Follow the README to acquire and process the sample before opening the explorer.')
        st.stop()
    df = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
    departments = sorted(df['department'].dropna().unique())
    all_dated = df.loc[df['date_begin_usable'].eq(True), 'begin_year']
    if all_dated.empty:
        st.info('No records with eligible dates in this sample.')
        st.stop()
    minimum, maximum = int(all_dated.min()), int(all_dated.max())
    st.sidebar.write('Quick demo selections')
    st.sidebar.button('Reset: all departments', on_click=set_filters, args=('All departments', (minimum, maximum)))
    for label, department in [('Painting media', 'European Paintings'), ('Asian culture labels', 'Asian Art')]:
        if department in departments:
            st.sidebar.button(label, on_click=set_filters, args=(department, (minimum, maximum)))
    selected = st.sidebar.selectbox('Department', ['All departments', *departments], key='department_filter')
    bounds = st.sidebar.slider('Recorded begin-year range', minimum, maximum, (minimum, maximum), key='year_filter')
    medium = st.sidebar.selectbox('Medium group', ['All medium groups', *sorted(df['medium_category'].dropna().unique())], key='medium_filter')
    base = df if selected == 'All departments' else df.loc[df['department'].eq(selected)]
    dated = base.loc[base['date_begin_usable'].eq(True)].copy()
    filtered = dated.loc[dated['begin_year'].between(*bounds)].copy()
    if medium != 'All medium groups':
        filtered = filtered.loc[filtered['medium_category'].eq(medium)].copy()
    st.sidebar.caption('Explorer tabs follow these filters. Zero/invalid date bounds are excluded. The guided live demo uses the full saved sample, as labeled.')
    st.metric('Matching records', f'{len(filtered):,}')
    st.caption(f'Date-eligible records before year/medium filters: {len(dated):,} of {len(base):,}. Select a question tab or run the guided demo.')
    if medium != 'All medium groups':
        st.caption('Medium proportions are conditional on this medium filter. Reset to All medium groups for the full medium mix.')
    if filtered.empty:
        st.info('No records match these filters. Widen the year range, reset the medium, or choose another department.')
        with st.expander('Run the guided demo using the full sample'):
            show_live_demo(df)
        return
    dates, media, cultures, objects, demo = st.tabs(['Q1 · Dates', 'Q2 · Media', 'Q3 · Cultures', 'Object browser', 'Live demo'])
    with dates:
        show_dates(filtered)
    with media:
        show_media(filtered)
    with cultures:
        show_cultures(filtered)
    with objects:
        show_objects(filtered)
    with demo:
        show_live_demo(df)


if __name__ == '__main__':
    main()
