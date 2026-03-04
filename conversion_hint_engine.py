import json
import os
import re
from typing import Dict, List, Optional


class ConversionHintEngine:
    TARGET_AUGMENTS = {"魔法转物理", "物理转魔法"}
    AUGMENT_ALIASES = {
        "魔法转物理": {"魔法转物理", "法转物", "法转物理", "魔转物", "魔转物理"},
        "物理转魔法": {"物理转魔法", "物转法", "物转魔", "物理转法术"}
    }

    def __init__(self, rules_path: str):
        self.rules_path = rules_path
        self.mechanics: Dict[str, Dict] = {}
        self.defaults: Dict[str, Dict] = {}
        self.heroes: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        self.mechanics = {}
        self.defaults = {}
        self.heroes = {}
        if not os.path.exists(self.rules_path):
            return
        with open(self.rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.mechanics = data.get("mechanics", {})
        self.defaults = data.get("defaults", {})
        self.heroes = data.get("heroes", {})

    @staticmethod
    def _to_text(items: List[str]) -> str:
        return " → ".join([x for x in items if x])

    @staticmethod
    def _normalize_augment(value: str) -> str:
        return re.sub(r"[\s：:]+", "", (value or ""))

    @classmethod
    def _canonical_augment(cls, value: str) -> Optional[str]:
        normalized = cls._normalize_augment(value)
        if not normalized:
            return None
        for canonical, aliases in cls.AUGMENT_ALIASES.items():
            normalized_aliases = {cls._normalize_augment(x) for x in aliases}
            if normalized in normalized_aliases:
                return canonical
        return None

    def _pick_trigger_augment(self, augment_names: List[str]) -> Optional[str]:
        for augment in augment_names:
            canonical = self._canonical_augment(augment)
            if canonical in self.TARGET_AUGMENTS:
                return canonical
        return None

    def get_recommendation(self, hero_name: str, augment_names: List[str]) -> Optional[Dict]:
        trigger = self._pick_trigger_augment(augment_names)
        if not trigger:
            return None
        hero_rule = self.heroes.get(hero_name, {})
        hero_trigger = self._canonical_augment(hero_rule.get("trigger_augment", "")) if hero_rule else None
        if hero_rule and hero_trigger and hero_trigger != trigger:
            hero_rule = {}
        base_rule = hero_rule if hero_rule else self.defaults.get(trigger, {})
        if not base_rule:
            return None
        mechanics = self.mechanics.get(trigger, {})
        core_items = base_rule.get("core_items", [])
        optional_items = base_rule.get("optional_items", [])
        reasons = list(base_rule.get("reasons", []))
        if mechanics.get("conversion_rate"):
            reasons.append(f"转化率: {mechanics['conversion_rate']}")
        if mechanics.get("bonus"):
            reasons.append(f"加成: {mechanics['bonus']}")
        rec = {
            "trigger_augment": trigger,
            "hero": hero_name,
            "fit_level": base_rule.get("fit_level", "通用"),
            "core_items": core_items,
            "optional_items": optional_items,
            "do_not_pick_if": base_rule.get("do_not_pick_if", []),
            "reasons": reasons,
            "confidence": base_rule.get("confidence", "中"),
            "stages": base_rule.get("stages", {}),
            "branches": base_rule.get("branches", {}),
            "is_default": not bool(hero_rule)
        }
        core_short = self._to_text(core_items[:3]) or "按通用保守出装"
        reason_short = (base_rule.get("reasons", []) or ["按技能频率和成型速度择优"])[0]
        risk_short = (base_rule.get("do_not_pick_if", []) or ["避免与当前主流出装冲突"])[0]
        rec["short_text"] = f"转化推荐[{trigger}]: {core_short}\n原因: {reason_short}\n风险: {risk_short}"
        return rec

    def format_detail_text(self, recommendation: Dict) -> str:
        if not recommendation:
            return ""
        trigger = recommendation.get("trigger_augment", "")
        confidence = recommendation.get("confidence", "中")
        fit_level = recommendation.get("fit_level", "通用")
        header = f"[转化策略] 海克斯:{trigger} | 适配:{fit_level} | 置信度:{confidence}"
        core = self._to_text(recommendation.get("core_items", []))
        optional = self._to_text(recommendation.get("optional_items", []))
        risks = "；".join(recommendation.get("do_not_pick_if", []))
        reasons = "；".join(recommendation.get("reasons", []))
        stages = recommendation.get("stages", {})
        branches = recommendation.get("branches", {})
        stage_text = (
            f"前期:{self._to_text(stages.get('early', []))} | "
            f"中期:{self._to_text(stages.get('mid', []))} | "
            f"后期:{self._to_text(stages.get('late', []))}"
        )
        branch_text = (
            f"顺风:{self._to_text(branches.get('ahead', []))} | "
            f"逆风:{self._to_text(branches.get('behind', []))}"
        )
        fallback = "默认策略: 未命中专属规则，采用通用保守构建。" if recommendation.get("is_default") else ""
        lines = [
            header,
            f"核心装: {core}",
            f"备选装: {optional}",
            f"原因: {reasons}",
            f"风险: {risks}",
            stage_text,
            branch_text
        ]
        if fallback:
            lines.append(fallback)
        return "\n".join(lines)

    def get_hint(self, hero_name: str, augment_names: List[str]) -> Optional[str]:
        recommendation = self.get_recommendation(hero_name, augment_names)
        if not recommendation:
            return None
        return recommendation.get("short_text")
