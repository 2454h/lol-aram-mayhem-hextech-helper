import json
import os
import tempfile
import unittest

from hextech_combo_provider import HextechComboProvider


class _MockResponse:
    def __init__(self, text="", json_data=None):
        self.text = text
        self._json_data = json_data

    def json(self):
        return self._json_data


class TestHextechComboProvider(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = self.tmp.name
        self.champions_path = os.path.join(self.data_dir, "champions.json")
        with open(self.champions_path, "w", encoding="utf-8") as f:
            json.dump({"星界游神": "Bard"}, f, ensure_ascii=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_fetch_and_cache_combo_recommendation(self):
        provider = HextechComboProvider(self.data_dir, self.champions_path)
        calls = {"count": 0}

        champion_html = """
        <div>Best Augment Combos</div>
        <tbody>
          <tr>
            <td><span class="font-bold text-primary">1</span></td>
            <td>
              <a href="/zh-CN/augments/1037"></a>
              <a href="/zh-CN/augments/1141"></a>
              <a href="/zh-CN/augments/1420"></a>
            </td>
            <td><span>T<!-- -->1</span></td>
          </tr>
          <tr>
            <td><span class="font-bold text-primary">2</span></td>
            <td>
              <a href="/zh-CN/augments/1048"></a>
              <a href="/zh-CN/augments/1136"></a>
              <a href="/zh-CN/augments/1390"></a>
            </td>
            <td><span>T<!-- -->2</span></td>
          </tr>
        </tbody>
        """

        def fake_get(url, timeout=0):
            calls["count"] += 1
            if "versions.json" in url:
                return _MockResponse(json_data=["16.4.1"])
            if "/champion/Bard.json" in url:
                return _MockResponse(json_data={"data": {"Bard": {"key": "432"}}})
            if "/champion-stats/432" in url:
                return _MockResponse(text=champion_html)
            if "/augments/1037" in url:
                return _MockResponse(text="<title>急救用具海克斯强化详情 - ARAM.GG</title>")
            if "/augments/1141" in url:
                return _MockResponse(text="<title>全是你海克斯强化详情 - ARAM.GG</title>")
            if "/augments/1420" in url:
                return _MockResponse(text="<title>奏鸣曲海克斯强化详情 - ARAM.GG</title>")
            if "/augments/1048" in url:
                return _MockResponse(text="<title>珠光护手海克斯强化详情 - ARAM.GG</title>")
            if "/augments/1136" in url:
                return _MockResponse(text="<title>乱拳打击海克斯强化详情 - ARAM.GG</title>")
            if "/augments/1390" in url:
                return _MockResponse(text="<title>邪恶势力海克斯强化详情 - ARAM.GG</title>")
            return _MockResponse(text="")

        provider.session.get = fake_get

        rec = provider.get_recommendation("星界游神", top_n=2)
        self.assertEqual(len(rec["combos"]), 2)
        self.assertEqual(rec["combos"][0]["tier"], "T1")
        self.assertEqual(rec["combos"][0]["augments"], ["急救用具", "全是你", "奏鸣曲"])
        self.assertFalse(rec["from_cache"])

        cache_file = os.path.join(self.data_dir, "hextech_combos_cache.json")
        self.assertTrue(os.path.exists(cache_file))

        first_call_count = calls["count"]
        rec_cached = provider.get_recommendation("星界游神", top_n=1)
        self.assertTrue(rec_cached["from_cache"])
        self.assertEqual(len(rec_cached["combos"]), 1)
        self.assertEqual(calls["count"], first_call_count)

    def test_top_n_limits_augment_resolution(self):
        provider = HextechComboProvider(self.data_dir, self.champions_path)
        calls = {"augment": 0}

        champion_html = """
        <div>Best Augment Combos</div>
        <tbody>
          <tr><td><span class="font-bold text-primary">1</span></td><td><a href="/zh-CN/augments/1001"></a><a href="/zh-CN/augments/1002"></a><a href="/zh-CN/augments/1003"></a></td><td><span>T<!-- -->1</span></td></tr>
          <tr><td><span class="font-bold text-primary">2</span></td><td><a href="/zh-CN/augments/1004"></a><a href="/zh-CN/augments/1005"></a><a href="/zh-CN/augments/1006"></a></td><td><span>T<!-- -->1</span></td></tr>
          <tr><td><span class="font-bold text-primary">3</span></td><td><a href="/zh-CN/augments/1007"></a><a href="/zh-CN/augments/1008"></a><a href="/zh-CN/augments/1009"></a></td><td><span>T<!-- -->1</span></td></tr>
        </tbody>
        """

        def fake_get(url, timeout=0):
            if "versions.json" in url:
                return _MockResponse(json_data=["16.4.1"])
            if "/champion/Bard.json" in url:
                return _MockResponse(json_data={"data": {"Bard": {"key": "432"}}})
            if "/champion-stats/432" in url:
                return _MockResponse(text=champion_html)
            if "/augments/" in url:
                calls["augment"] += 1
                return _MockResponse(text="<title>测试强化海克斯强化详情 - ARAM.GG</title>")
            return _MockResponse(text="")

        provider.session.get = fake_get
        rec = provider.get_recommendation("星界游神", top_n=1)
        self.assertEqual(len(rec["combos"]), 1)
        self.assertEqual(calls["augment"], 3)


if __name__ == "__main__":
    unittest.main()
