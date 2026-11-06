
import unittest

import pandas as pd

from process_data import build_dataframe, centuries, classify_medium, temporal_summary


# Synthetic edge cases are test fixtures, not research data.
class ProcessingTests(unittest.TestCase):

    def test_century_boundaries(self):
        values = pd.Series([-101, -100, -1, 0, 1, 100, 101, None, 1.5])
        actual = centuries(values)
        self.assertEqual(actual.iloc[[0, 1, 2, 4, 5, 6]].tolist(), [-2, -1, -1, 1, 1, 2])
        self.assertTrue(actual.iloc[[3, 7, 8]].isna().all())


    def test_date_flags_and_missing_nationality_do_not_delete_records(self):
        records = [
            {'objectID': 1, 'department': 'A', 'objectBeginDate': 0, 'objectEndDate': 0, 'objectDate': ' '},
            {'objectID': 2, 'department': 'A', 'objectBeginDate': 0, 'objectEndDate': 25, 'objectDate': 'BCE–CE'},
            {'objectID': 3, 'department': 'A', 'objectBeginDate': 100, 'objectEndDate': 50},
            {'objectID': 4, 'department': 'A', 'objectBeginDate': -100, 'objectEndDate': -50, 'artistNationality': ''},
            {'objectID': 5, 'department': 'A', 'objectBeginDate': 100, 'objectEndDate': 800},
        ]
        df = build_dataframe(records)
        self.assertEqual(len(df), 5)
        self.assertEqual(df['date_begin_usable'].tolist(), [False, False, False, True, True])
        self.assertTrue(df.loc[0, 'date_unknown'])
        self.assertTrue(df.loc[1, 'date_zero_review'])
        self.assertTrue(df.loc[2, 'date_reversed'])
        self.assertTrue(df.loc[4, 'date_wide_span'])
        self.assertEqual(temporal_summary(df)['valid_date_records'].iloc[0], 2)
        self.assertEqual(temporal_summary(df, exclude_wide=True)['valid_date_records'].iloc[0], 1)


    def test_medium_precedence(self):
        actual = classify_medium(pd.Series(['Oil on copper', 'Terracotta', 'Silk', 'Bronze', 'something else', pd.NA]))
        self.assertEqual(actual.tolist(), ['oil_painting', 'ceramic', 'textile', 'bronze', 'other', 'unknown'])


    # Hand-checkable quartiles verify the numerical interpretation.
    def test_numpy_statistics(self):
        df = build_dataframe([{'objectID': i, 'department': 'A', 'objectBeginDate': y, 'objectEndDate': y}
                              for i, y in enumerate([100, 200, 300, 400], 1)])
        row = temporal_summary(df).iloc[0]
        self.assertEqual(row['median_begin_year'], 250)
        self.assertEqual(row['q1_begin_year'], 175)
        self.assertEqual(row['q3_begin_year'], 325)
        self.assertEqual(row['iqr_years'], 150)


if __name__ == '__main__':
    unittest.main()
