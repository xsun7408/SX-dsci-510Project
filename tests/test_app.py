"""Exercise filtering with small synthetic fixtures, not the research cache."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from process_data import build_dataframe

ROOT = Path(__file__).resolve().parents[1]


class AppTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'objects_clean.csv'
        records = []
        for object_id, department, year in [(1, 'European Paintings', 1800), (2, 'European Paintings', 1900),
                                            (3, 'Asian Art', 1000), (4, 'Greek and Roman Art', -500), (5, 'Asian Art', 0)]:
            records.append({'objectID': object_id, 'department': department, 'objectBeginDate': year,
                            'objectEndDate': year, 'objectDate': '' if year == 0 else str(year),
                            'medium': 'Bronze', 'title': f'Test object {object_id}',
                            'culture': '', 'artistDisplayName': ''})
        build_dataframe(records).to_csv(self.path, index=False)
        self.environment = patch.dict(os.environ, {'MET_DATA_PATH': str(self.path)})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def app(self):
        return AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()

    def test_filters_change_counts_and_object_rows(self):
        at = self.app()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value, '4')
        at.sidebar.selectbox[0].set_value('European Paintings').run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value, '2')
        at.sidebar.slider[0].set_value((1850, 1900)).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value, '1')
        self.assertEqual(at.dataframe[-1].value['objectID'].tolist(), [2])
        self.assertEqual(at.metric[1].value, '1900')

    def test_empty_selection_has_no_stale_examples(self):
        at = self.app()
        at.sidebar.selectbox[0].set_value('European Paintings').run()
        at.sidebar.slider[0].set_value((-500, -500)).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value, '0')
        self.assertIn('No records match', at.info[0].value)
        self.assertEqual(len(at.dataframe), 0)

    def test_missing_processed_data_has_actionable_message(self):
        self.path.unlink()
        at = self.app()
        self.assertFalse(at.exception)
        self.assertIn('Processed sample not found', at.error[0].value)
        self.assertEqual(len(at.metric), 0)


if __name__ == '__main__':
    unittest.main()
