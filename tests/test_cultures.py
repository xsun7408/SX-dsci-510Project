"""Test diversity semantics and coverage without using invented research results."""
import unittest

import numpy as np
import pandas as pd

from analyze_cultures import culture_summary, diversity_from_counts, normalize_culture


class CultureTests(unittest.TestCase):
    def fixture(self):
        return pd.DataFrame([
            [1, 'A', 'Greek, Attic', 1, True, False],
            [2, 'A', 'Greek, Attic', 1, True, False],
            [3, 'A', 'Roman', 1, True, True],
            [4, 'A', '', 1, True, False],
            [5, 'B', None, 1, True, False],
            [6, 'B', ' ', 1, True, False],
            [7, 'A', 'Greek or Roman', 2, True, False],
            [8, 'A', 'Roman', 0, False, False],
        ], columns=['objectID', 'department', 'culture', 'century', 'date_begin_usable', 'date_wide_span'])

    def test_known_probability_distributions_and_empty_rows(self):
        with np.errstate(divide='raise', invalid='raise'):
            result = diversity_from_counts([[5, 5, 0], [10, 0, 0], [0, 0, 0]])
        self.assertAlmostEqual(result['shannon_nats'][0], np.log(2))
        self.assertAlmostEqual(result['gini_simpson'][0], .5)
        self.assertAlmostEqual(result['effective_labels'][0], 2)
        self.assertEqual(result['shannon_nats'][1], 0)
        self.assertEqual(result['gini_simpson'][1], 0)
        self.assertEqual(result['effective_labels'][1], 1)
        self.assertTrue(np.isnan(result['shannon_nats'][2]))
        self.assertTrue(np.isnan(result['gini_simpson'][2]))

    def test_invalid_count_matrices(self):
        for values in [[1, 2], [[-1, 2]], [[np.nan, 1]]]:
            with self.assertRaises(ValueError):
                diversity_from_counts(values)

    def test_coverage_denominator_and_exact_labels(self):
        summary, labels = culture_summary(self.fixture(), by_century=True, min_documented=2, min_coverage=.8)
        a = summary.loc[summary.department.eq('A') & summary.century.eq(1)].iloc[0]
        self.assertEqual(a.records, 4)
        self.assertEqual(a.documented, 3)
        self.assertEqual(a.coverage, .75)
        self.assertFalse(a.sufficient_n)
        b = summary.loc[summary.department.eq('B')].iloc[0]
        self.assertEqual(b.coverage, 0)
        self.assertTrue(np.isnan(b.shannon_nats))
        self.assertIn('Greek, Attic', labels.culture_label.tolist())
        self.assertNotIn('Greek', labels.culture_label.tolist())
        self.assertEqual(int(labels['count'].sum()), 4)

    def test_date_and_uncertainty_sensitivity(self):
        all_summary, _ = culture_summary(self.fixture())
        self.assertEqual(all_summary.records.sum(), 8)
        wide, _ = culture_summary(self.fixture(), by_century=True, exclude_wide=True)
        self.assertEqual(wide.records.sum(), 6)
        certain, labels = culture_summary(self.fixture(), by_century=True, exclude_uncertain=True)
        group = certain.loc[certain.department.eq('A') & certain.century.eq(2)].iloc[0]
        self.assertEqual(group.records, 1)
        self.assertEqual(group.documented, 0)
        self.assertTrue(np.isnan(group.shannon_nats))
        self.assertNotIn('Greek or Roman', labels.culture_label.tolist())

    def test_normalization_and_empty_input(self):
        labels = normalize_culture(pd.Series(['  Greek,   Attic ', 'Unknown', '', None]))
        self.assertEqual(labels.iloc[0], 'Greek, Attic')
        self.assertTrue(labels.iloc[1:].isna().all())
        empty = self.fixture().iloc[:0]
        summary, labels = culture_summary(empty, by_century=True)
        self.assertTrue(summary.empty)
        self.assertTrue(labels.empty)


if __name__ == '__main__':
    unittest.main()
