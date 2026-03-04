import os
import unittest

from conversion_hint_engine import ConversionHintEngine


class TestConversionHintEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rules_path = os.path.join(base_dir, "data", "conversion_rules.json")
        cls.engine = ConversionHintEngine(rules_path)

    def test_non_target_augment_returns_none(self):
        rec = self.engine.get_recommendation("探险家", ["魔法飞弹", "珠光护手"])
        self.assertIsNone(rec)

    def test_target_augment_with_specific_hero(self):
        rec = self.engine.get_recommendation("探险家", ["魔法转物理"])
        self.assertIsNotNone(rec)
        self.assertEqual(rec["trigger_augment"], "魔法转物理")
        self.assertEqual(rec["hero"], "探险家")
        self.assertFalse(rec["is_default"])
        self.assertTrue(rec["core_items"])
        self.assertTrue(rec["reasons"])
        self.assertIn("风险:", rec["short_text"])

    def test_target_augment_with_unknown_hero_uses_default(self):
        rec = self.engine.get_recommendation("九尾妖狐", ["物理转魔法"])
        self.assertIsNotNone(rec)
        self.assertEqual(rec["trigger_augment"], "物理转魔法")
        self.assertTrue(rec["is_default"])
        self.assertTrue(rec["core_items"])
        self.assertTrue(rec["stages"])
        self.assertTrue(rec["branches"])

    def test_detail_text_contains_explainability_fields(self):
        rec = self.engine.get_recommendation("德玛西亚之力", ["物理转魔法"])
        text = self.engine.format_detail_text(rec)
        self.assertIn("海克斯:物理转魔法", text)
        self.assertIn("置信度:", text)
        self.assertIn("原因:", text)
        self.assertIn("风险:", text)
        self.assertIn("顺风:", text)
        self.assertIn("逆风:", text)

    def test_new_physical_to_magic_heroes_loaded(self):
        rec = self.engine.get_recommendation("放逐之刃", ["物理转魔法"])
        self.assertIsNotNone(rec)
        self.assertEqual(rec["trigger_augment"], "物理转魔法")
        self.assertFalse(rec["is_default"])
        self.assertIn("海克斯火箭腰带", rec["core_items"])


if __name__ == "__main__":
    unittest.main()
