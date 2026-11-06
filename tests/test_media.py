"""Check medium priorities, group denominators, and sparse-date sensitivity."""
import unittest

import numpy as np
import pandas as pd

from analyze_media import medium_composition, sensitivity_changes
from process_data import classify_medium


class MediumTests(unittest.TestCase):
    def fixture(self):
        return pd.DataFrame([
            ['A', 18, 'bronze', True, True],
            ['A', 18, 'ceramic', True, False],
            ['A', 18, 'ceramic', True, False],
            ['A', 19, 'unknown', True, False],
            ['B', 18, 'bronze', True, False],
            ['B', 18, 'bronze', False, False],
        ], columns=['department', 'century', 'medium_category', 'date_begin_usable', 'date_wide_span'])

    def test_priority_for_composite_media(self):
        media = pd.Series(['Ink and color on silk', 'Porcelain with polychrome enamels', 'Oil on copper',
                           'Clay with glaze', 'Unfired clay with pigment', 'Ivory', 'unidentified material'])
        self.assertEqual(classify_medium(media).tolist(), ['ink_watercolor_print', 'ceramic', 'oil_painting',
                                                         'ceramic', 'clay_earth', 'ivory_bone_horn', 'other'])

    def test_denominators_are_department_and_century_specific(self):
        result = medium_composition(self.fixture(), min_count=2)
        a = result.loc[result.department.eq('A') & result.century.eq(18)]
        self.assertEqual(a.records.unique().tolist(), [3])
        self.assertAlmostEqual(a.loc[a.medium_category.eq('bronze'), 'share'].iloc[0], 1 / 3)
        self.assertAlmostEqual(a.loc[a.medium_category.eq('ceramic'), 'share'].iloc[0], 2 / 3)
        totals = result.groupby(['department', 'century'])['share'].sum()
        self.assertTrue(np.allclose(totals, 1))
        self.assertEqual(int(result['count'].sum()), 5)
        sparse = result.loc[result.department.eq('A') & result.century.eq(19)]
        self.assertFalse(sparse.sufficient_n.any())
        self.assertEqual(sparse.loc[sparse.medium_category.eq('unknown'), 'share'].iloc[0], 1)

    def test_sensitivity_keeps_zero_categories_and_checks_both_group_sizes(self):
        data = self.fixture()
        main = medium_composition(data, min_count=2)
        narrow = medium_composition(data, min_count=2, exclude_wide=True)
        changes = sensitivity_changes(main, narrow)
        bronze = changes.loc[changes.medium_category.eq('bronze')].iloc[0]
        self.assertEqual(bronze['share_excluding_wide'], 0)
        self.assertAlmostEqual(bronze['change_percentage_points'], -100 / 3)
        self.assertTrue(changes.department.eq('A').all())
        self.assertTrue(changes.century.eq(18).all())

    def test_empty_and_invalid_threshold(self):
        data = self.fixture()
        data['date_begin_usable'] = False
        self.assertTrue(medium_composition(data).empty)
        with self.assertRaises(ValueError):
            medium_composition(data, min_count=0)


if __name__ == '__main__':
    unittest.main()
