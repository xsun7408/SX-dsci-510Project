"""Audience-driven presentation controls, with live and saved evidence kept distinct."""
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

from acquire import MetClient, fetch_object
from analyze_cultures import culture_summary
from process_data import temporal_summary


# One bounded live request per click; do not silently use a cached response.
def fetch_live_example(object_id):
    client = MetClient(interval=1, attempts=1, timeout=(3, 8))
    try:
        return fetch_object(client, int(object_id))
    finally:
        client.session.close()


def show_live_demo(df):
    st.subheader('Guided audience-driven demo')
    st.caption('This guided demo uses the full saved sample, independently of the explorer sidebar filters. Only the live-request button contacts the API.')
    step = st.radio('Demo step', ['Live API', 'Predict and compare', 'Culture calculator'], horizontal=True, key='demo_step')
    if step == 'Live API':
        departments = sorted(df['department'].dropna().unique())
        department = st.selectbox('Live example department', departments, key='live_department')
        example = df.loc[df['department'].eq(department)].sort_values('objectID').iloc[0]
        object_id = int(example['objectID'])
        st.write(f'Request one real object: {object_id} — {example["title"]}')
        st.caption('The research script obtained departments, candidate IDs, and the fixed sample separately. This button refreshes one object-detail endpoint; it does not change the research data.')
        if st.button('Fetch this object from the API now', key='fetch_live'):
            # Clear earlier success first, so a failed refresh cannot look like a successful new call.
            st.session_state.pop('live_response', None)
            st.session_state.pop('live_failure', None)
            try:
                with st.spinner('Requesting fresh object metadata…'):
                    record = fetch_live_example(object_id)
                st.session_state['live_response'] = {'objectID': object_id, 'received_at_utc': datetime.now(timezone.utc).isoformat(), 'record': record}
            except (requests.RequestException, ValueError) as exc:
                status = exc.response.status_code if isinstance(exc, requests.RequestException) and exc.response is not None else None
                st.session_state['live_failure'] = {'objectID': object_id, 'message': f'HTTP {status}' if status else type(exc).__name__}
        response = st.session_state.get('live_response')
        failure = st.session_state.get('live_failure')
        if response and response['objectID'] == object_id:
            st.success('Fresh API response received successfully.')
            st.caption(f'Received at {response["received_at_utc"]} (UTC). The JSON below came from this live request.')
            st.json(response['record'], expanded=False)
            st.dataframe(pd.DataFrame([response['record']]).reindex(columns=['objectID', 'title', 'department', 'objectDate', 'medium']), hide_index=True)
        elif failure and failure['objectID'] == object_id:
            st.error(f'Live API request did not succeed ({failure["message"]}). The saved evidence below is not a fresh API response.')
        with st.expander('Saved processed metadata — offline evidence, not a live response'):
            fields = ['objectID', 'title', 'department', 'objectDate', 'medium', 'culture']
            st.json({field: None if pd.isna(example[field]) else int(example[field]) if field == 'objectID' else str(example[field]) for field in fields})
    elif step == 'Predict and compare':
        summary = temporal_summary(df)
        options = summary.loc[summary['valid_date_records'].gt(0), 'department'].tolist()
        prediction = st.radio('Which department has the earliest median recorded begin year?', options, index=None, key='prediction')
        st.caption('Ask the audience to predict, then reveal the calculation from the fixed sample. Recorded start dates are interval bounds, not exact creation dates.')
        if st.button('Reveal the department comparison', disabled=prediction is None, key='reveal_comparison'):
            available = summary.loc[summary['valid_date_records'].gt(0)]
            minimum = available['median_begin_year'].min()
            winners = available.loc[available['median_begin_year'].eq(minimum), 'department'].tolist()
            st.success(f'Earliest sample median: {", ".join(winners)} ({minimum:g}).')
            st.write('Your prediction matches the calculation.' if prediction in winners else 'The calculation differs from your prediction; compare the table below.')
            st.dataframe(summary, hide_index=True)
            st.bar_chart(summary.set_index('department')['median_begin_year'])
            with st.expander('Show the NumPy calculation'):
                st.code('years = eligible_department_years.to_numpy(dtype=float)\nmedian = np.median(years)\nq1, q3 = np.percentile(years, [25, 75])\niqr = q3 - q1', language='python')
    else:
        department = st.selectbox('Culture calculator department', sorted(df['department'].dropna().unique()), key='culture_demo_department')
        certain_only = st.checkbox('Exclude explicitly uncertain culture labels', key='demo_certain_only')
        group = df.loc[df['department'].eq(department)]
        summary, labels = culture_summary(group, exclude_uncertain=certain_only)
        row = summary.iloc[0]
        st.write(f'Documented labels: {int(row.documented)} / {int(row.records)} ({100*row.coverage:.1f}%).')
        if row.documented == 0:
            st.info('All culture labels are missing here. Shannon diversity is undefined, not zero. Artist nationality is not substituted.')
        else:
            a, b = st.columns(2)
            a.metric('Shannon entropy (nats)', f'{row.shannon_nats:.3f}')
            b.metric('Gini-Simpson index', f'{row.gini_simpson:.3f}')
            st.dataframe(labels.sort_values('count', ascending=False).head(10), hide_index=True)
            with st.expander('Show the probability and NumPy steps'):
                st.code('p = counts / counts.sum(axis=1, keepdims=True)\nlog_p = np.log(p, out=np.zeros_like(p), where=p > 0)\nH = -(p * log_p).sum(axis=1)\ngini_simpson = 1 - (p ** 2).sum(axis=1)', language='python')
        st.caption('This calculator includes all sampled records in the chosen department, not just date-eligible rows. Indices describe catalog labels, not societal diversity.')
