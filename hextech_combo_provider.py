import json
import os
import re
import subprocess
import threading
from datetime import datetime, timedelta, timezone

import requests


class HextechComboProvider:
    def __init__(self, data_dir, champions_path):
        self.data_dir = data_dir
        self.champions_path = champions_path
        self.cache_path = os.path.join(self.data_dir, "hextech_combos_cache.json")
        self.cache_hours = 24
        self.session = requests.Session()
        self.hero_to_en = self._load_hero_map()
        self.cache = self._load_cache()

    def get_recommendation(self, hero_cn, top_n=3):
        if not hero_cn:
            return {"hero": hero_cn, "combos": [], "from_cache": False}

        cached = self._get_cached(hero_cn)
        if cached:
            return {"hero": hero_cn, "combos": cached[:top_n], "from_cache": True}

        champion_key = self._get_champion_key(hero_cn)
        if not champion_key:
            return {"hero": hero_cn, "combos": [], "from_cache": False}

        combos = self._fetch_combos(champion_key, top_n=top_n)
        if combos:
            self.cache.setdefault("heroes", {})[hero_cn] = {
                "updated_at": self._now_iso(),
                "champion_key": champion_key,
                "combos": combos
            }
            self._save_cache()
        return {"hero": hero_cn, "combos": combos[:top_n], "from_cache": False}

    def prefetch_recommendation(self, hero_cn, top_n=3):
        if not hero_cn:
            return
        if self._get_cached(hero_cn):
            return
        worker = threading.Thread(
            target=self.get_recommendation,
            args=(hero_cn, top_n),
            daemon=True
        )
        worker.start()

    def format_for_overlay(self, recommendation):
        combos = recommendation.get("combos", []) if recommendation else []
        if not combos:
            return ""
        lines = ["海克斯组合推荐"]
        for item in combos:
            combo = " + ".join(item.get("augments", []))
            lines.append(f"{item.get('rank')}. {combo} ({item.get('tier')})")
        return "\n".join(lines)

    def format_for_console(self, recommendation):
        if not recommendation:
            return ""
        combos = recommendation.get("combos", [])
        if not combos:
            return "海克斯组合推荐: 暂无可用数据"
        lines = ["=== 海克斯组合推荐 ==="]
        for item in combos:
            combo = " + ".join(item.get("augments", []))
            lines.append(f"No.{item.get('rank')} | {combo} | {item.get('tier')}")
        lines.append(f"来源: hextech.dtodo.cn | 缓存: {'是' if recommendation.get('from_cache') else '否'}")
        return "\n".join(lines)

    def _fetch_combos(self, champion_key, top_n=3):
        url = f"https://hextech.dtodo.cn/zh-CN/champion-stats/{champion_key}"
        try:
            html = self._get_text(url)
            if not html:
                return []
            section = re.search(r"Best Augment Combos.*?<tbody[^>]*>(.*?)</tbody>", html, re.S)
            if not section:
                section = re.search(r"推荐海克斯组合.*?<tbody[^>]*>(.*?)</tbody>", html, re.S)
            if not section:
                section = re.search(r"最佳海克斯组合.*?<tbody[^>]*>(.*?)</tbody>", html, re.S)
            if not section:
                return []
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", section.group(1), re.S)
            if top_n and top_n > 0:
                rows = rows[:top_n]
            combos = []
            for row in rows:
                rank_match = re.search(r'font-bold text-primary">(\d+)<', row)
                tier_match = re.search(r">T(?:<!-- -->)?(\d)<", row)
                augment_ids = re.findall(r"/(?:[a-zA-Z-]+/)?augments/(\d+)", row)
                if not rank_match or not tier_match or len(augment_ids) < 3:
                    continue
                augments = [self._resolve_augment_name(augment_ids[i]) for i in range(3)]
                combos.append({
                    "rank": int(rank_match.group(1)),
                    "tier": f"T{tier_match.group(1)}",
                    "augments": augments
                })
            combos.sort(key=lambda x: x["rank"])
            return combos
        except Exception:
            return []

    def _resolve_augment_name(self, augment_id):
        augment_cache = self.cache.setdefault("augment_names", {})
        cached = augment_cache.get(str(augment_id))
        if cached and self._is_fresh(cached.get("updated_at"), days=7):
            return cached.get("name", f"#{augment_id}")

        zh_url = f"https://hextech.dtodo.cn/zh-CN/augments/{augment_id}"
        try:
            html = self._get_text(zh_url)
            if not html:
                return f"#{augment_id}"
            title_match = re.search(r"<title>(.*?)</title>", html, re.S)
            if not title_match:
                return f"#{augment_id}"
            title = title_match.group(1).strip()
            name = title.split("海克斯强化详情")[0].split("ARAM")[0].strip(" -|")
            if not name:
                name = f"#{augment_id}"
            augment_cache[str(augment_id)] = {"name": name, "updated_at": self._now_iso()}
            return name
        except Exception:
            return f"#{augment_id}"

    def _get_champion_key(self, hero_cn):
        key_cache = self.cache.setdefault("champion_keys", {})
        if hero_cn in key_cache:
            return key_cache[hero_cn]

        en_name = self.hero_to_en.get(hero_cn)
        if not en_name:
            return None
        version = self._get_latest_ddragon_version()
        if not version:
            return None

        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion/{en_name}.json"
        try:
            data = self.session.get(url, timeout=15).json()
            champ = data.get("data", {}).get(en_name)
            if not champ:
                return None
            key = int(champ.get("key"))
            key_cache[hero_cn] = key
            self._save_cache()
            return key
        except Exception:
            return None

    def _get_latest_ddragon_version(self):
        version = self.cache.get("ddragon_version")
        version_updated = self.cache.get("ddragon_updated_at")
        if version and self._is_fresh(version_updated, days=3):
            return version
        try:
            versions = self.session.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=10).json()
            if not versions:
                return None
            self.cache["ddragon_version"] = versions[0]
            self.cache["ddragon_updated_at"] = self._now_iso()
            self._save_cache()
            return versions[0]
        except Exception:
            return version

    def _get_cached(self, hero_cn):
        hero_cache = self.cache.get("heroes", {}).get(hero_cn)
        if not hero_cache:
            return None
        if not self._is_fresh(hero_cache.get("updated_at"), hours=self.cache_hours):
            return None
        return hero_cache.get("combos", [])

    def _load_hero_map(self):
        try:
            with open(self.champions_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _load_cache(self):
        if not os.path.exists(self.cache_path):
            return {"heroes": {}, "augment_names": {}, "champion_keys": {}}
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("heroes", {})
            data.setdefault("augment_names", {})
            data.setdefault("champion_keys", {})
            return data
        except Exception:
            return {"heroes": {}, "augment_names": {}, "champion_keys": {}}

    def _save_cache(self):
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _get_text(self, url, timeout=20):
        try:
            return self.session.get(url, timeout=timeout).text
        except Exception:
            pass
        try:
            cp = subprocess.run(
                ["curl.exe", "-L", "--silent", "--show-error", "--max-time", str(timeout), url],
                capture_output=True,
                timeout=timeout + 3
            )
            if cp.returncode != 0:
                return ""
            return cp.stdout.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    @staticmethod
    def _is_fresh(timestamp, hours=0, days=0):
        if not timestamp:
            return False
        try:
            updated = datetime.fromisoformat(timestamp)
        except Exception:
            return False
        now = datetime.now(timezone.utc)
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        return now - updated <= timedelta(hours=hours, days=days)

    @staticmethod
    def _now_iso():
        return datetime.now(timezone.utc).isoformat()
