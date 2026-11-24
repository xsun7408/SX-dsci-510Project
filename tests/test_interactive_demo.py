"""Verify audience controls and honest separation of live vs saved metadata."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import requests
from streamlit.testing.v1 import AppTest

from process_data import build_dataframe

ROOT = Path(__file__).resolve().parents[1]


class InteractiveDemoTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'sample.csv'
        records = []
        for object_id, department, year, title in [(1, 'Asian Art', 1000, 'Moon over lake'),
                                                   (2, 'European Paintings', 1800, 'Portrait'),
                                                   (3, 'Greek and Roman Art', -500, 'Vase')]:
            records.append({'objectID': object_id, 'department': department, 'objectBeginDate': year,
                            'objectEndDate': year, 'objectDate': str(year), 'title': title,
                            'medium': 'Bronze', 'culture': department, 'artistDisplayName': 'Test artist'})
        build_dataframe(records).to_csv(self.path, index=False)
        environment = patch.dict(os.environ, {'MET_DATA_PATH': str(self.path)})
        environment.start()
        self.addCleanup(environment.stop)

    def app(self):
        return AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()

    def test_no_automatic_api_call_and_live_success_is_explicit(self):
        with patch('interactive_demo.fetch_live_example', return_value={'objectID': 1, 'title': 'Fresh title'}) as fetch:
            at = self.app()
            fetch.assert_not_called()
            at.button(key='fetch_live').click().run()
            self.assertFalse(at.exception)
            fetch.assert_called_once_with(1)
            self.assertTrue(any('Fresh API response received' in item.value for item in at.success))
            self.assertEqual(at.session_state['live_response']['record']['title'], 'Fresh title')

    def test_failed_refresh_clears_old_success(self):
        with patch('interactive_demo.fetch_live_example', return_value={'objectID': 1, 'title': 'Fresh title'}):
            at = self.app()
            at.button(key='fetch_live').click().run()
        with patch('interactive_demo.fetch_live_example', side_effect=requests.ConnectionError('offline')):
            at.button(key='fetch_live').click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Live API request did not succeed' in item.value for item in at.error))
        self.assertFalse(any('Fresh API response received' in item.value for item in at.success))
        self.assertNotIn('live_response', at.session_state)

    def test_prediction_reveals_computed_winner(self):
        at = self.app()
        at.radio(key='demo_step').set_value('Predict and compare').run()
        self.assertTrue(at.button(key='reveal_comparison').disabled)
        at.radio(key='prediction').set_value('Greek and Roman Art').run()
        at.button(key='reveal_comparison').click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Greek and Roman Art (-500)' in item.value for item in at.success))
        self.assertTrue(any('Your prediction matches' in item.value for item in at.markdown))

    def test_search_and_presets_update_real_selection(self):
        at = self.app()
        at.text_input(key='object_search').set_value('Moon').run()
        self.assertFalse(at.exception)
        self.assertEqual(at.dataframe[-1].value['objectID'].tolist(), [1])
        at.text_input(key='object_search').set_value('').run()
        next(button for button in at.sidebar.button if button.label == 'Painting media').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value, '1')
        self.assertEqual(at.dataframe[-1].value['objectID'].tolist(), [2])

    def test_medium_filter_is_used_for_statistics_and_metadata(self):
        data = pd.read_csv(self.path)
        data.loc[data.objectID.eq(1), 'medium_category'] = 'textile'
        data.to_csv(self.path, index=False)
        at = self.app()
        at.sidebar.selectbox(key='medium_filter').set_value('textile').run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value, '1')
        self.assertEqual(at.metric[1].value, '1000')
        self.assertEqual(at.dataframe[-1].value['objectID'].tolist(), [1])


if __name__ == '__main__':
    unittest.main()
