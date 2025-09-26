import os
import json
import re
from typing import List

from rapidfuzz import fuzz, process as rf_process


class ConsolidationConfig:
    def __init__(self, base_dir: str, sfw_mode: bool = False):
        self.base_dir = base_dir
        self.sfw_mode = sfw_mode
        # Resolve data directory with backward-compatible fallback
        self.data_dir = self._resolve_data_dir(base_dir)
        self.allowlist = self._read_lines(os.path.join(self.data_dir, "allowlists", "allowlist.txt"))
        self.weightable = self._read_lines(os.path.join(self.data_dir, "allowlists", "weightable_tags.txt"))
        self.media = self._read_lines(os.path.join(self.data_dir, "allowlists", "media_tags.txt"))
        self.drift = self._read_lines(os.path.join(self.data_dir, "allowlists", "generic_drift.txt"))
        with open(os.path.join(self.data_dir, "maps", "alias_map.json"), "r", encoding="utf-8") as f:
            self.alias_map = json.load(f)
        with open(os.path.join(self.data_dir, "features", "modifiers.json"), "r", encoding="utf-8") as f:
            self.modifiers = json.load(f)

    @staticmethod
    def _read_lines(path: str) -> List[str]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return [l.strip() for l in f if l.strip()]
        except OSError:
            return []

    @staticmethod
    def _resolve_data_dir(base_dir: str) -> str:
        """Choose the data directory that actually contains the allowlist sentinel.

        Preference order:
        1) <base_dir>/data (new layout) — only if allowlists/allowlist.txt exists
        2) <base_dir>/essence-extractor/data (legacy) — if sentinel exists there
        Fallback to <base_dir>/data for stable joins if no sentinel found.
        """
        new_dir = os.path.join(base_dir, "data")
        legacy_dir = os.path.join(base_dir, "essence-extractor", "data")
        sentinel = os.path.join("allowlists", "allowlist.txt")

        def has_sentinel(d: str) -> bool:
            return os.path.isfile(os.path.join(d, sentinel))

        if has_sentinel(new_dir):
            return new_dir
        if has_sentinel(legacy_dir):
            return legacy_dir
        # Fallback to new_dir path for stable structure even if empty
        return new_dir


def _split_and_clean(text: str) -> List[str]:
    parts: List[str] = []
    for raw in text.split(","):
        t = raw.strip()
        if t:
            parts.append(t)
    return parts


def _alias_or_canonical(token: str, cfg: ConsolidationConfig) -> str:
    key = token.lower().replace("_", " ")
    if key in cfg.allowlist:
        return key
    for aliases_csv, canon in cfg.alias_map.items():
        for alias in [a.strip() for a in aliases_csv.split(",")]:
            if key == alias:
                return canon
    match = rf_process.extractOne(key, cfg.allowlist, scorer=fuzz.QRatio)
    if match:
        candidate, score, _ = match
        if score >= 90:
            return candidate
    return key


def _dedupe_near(tokens: List[str], threshold: int = 92) -> List[str]:
    kept: List[str] = []
    for t in tokens:
        if not t:
            continue
        is_dup = False
        for k in kept:
            try:
                if fuzz.QRatio(t, k) >= threshold:
                    is_dup = True
                    break
            except (ValueError, TypeError):
                is_dup = False
                break
        if not is_dup:
            kept.append(t)
    return kept


def _soft_compact_fallback(input_text: str, cfg: ConsolidationConfig) -> str:
    toks = _split_and_clean(input_text)
    if not toks:
        return ""
    original_n = len(toks)
    min_keep = max(10, int(round(0.35 * original_n)))
    target = max(min_keep, int(round(0.85 * original_n)))
    keep: List[str] = []
    drift_set = set(x.lower() for x in (cfg.drift or []))
    for t in toks:
        key = t.lower()
        if len(keep) >= target:
            keep.append(t)
            continue
        if key in drift_set:
            continue
        keep.append(t)
    if not keep or ", ".join(keep) == input_text:
        sorted_text = ", ".join(sorted(toks, key=lambda s: s.lower()))
        return sorted_text
    return ", ".join(keep)


def consolidate_algorithmic(input_text: str, cfg: ConsolidationConfig) -> str:
    tokens = _split_and_clean(input_text)
    if not tokens:
        return ""

    mapped: List[str] = []
    for tok in tokens:
        canon = _alias_or_canonical(tok, cfg)
        mapped.append(canon)

    pc_pool = {
        "solo", "duo", "group", "1girl", "1boy", "2girls", "2boys", "3girls", "3boys",
        "4girls", "4boys", "multiple girls", "multiple boys"
    }
    pc_seen = [t for t in mapped if t in pc_pool]
    if len(pc_seen) > 1:
        keep = max(pc_seen, key=len)
        mapped = [t for t in mapped if t not in pc_pool] + [keep]

    mapped = [t for t in mapped if t != "hair"]

    norm_tokens: List[str] = []
    for t in mapped:
        x = t
        x = re.sub(r"\bgloss lipstick\b", "lip gloss", x)
        norm_tokens.append(x)

    def _merge_descriptor_groups(tokens: List[str]) -> List[str]:
        nouns = [
            "pubic hair", "armpit hair", "lip gloss",
            "breasts", "ass", "skin", "areolas", "penis",
            "eyeliner", "blush", "eyeshadow", "brows", "fingernails", "lipstick",
        ]
        noun_pattern = r"^(?P<desc>.+?)\s+(?P<noun>" + "|".join([re.escape(n) for n in nouns]) + r")$"
        lip_gloss_present = any(t == "lip gloss" or t.endswith(" lip gloss") for t in tokens)

        groups = {}
        indices_by_noun = {}
        for idx, t in enumerate(tokens):
            m = re.match(noun_pattern, t)
            if not m:
                continue
            noun = m.group("noun")
            desc = m.group("desc").strip()
            if noun == "lipstick" and lip_gloss_present:
                noun = "lip gloss"
            if noun not in groups:
                groups[noun] = {"descs": [], "first_idx": idx}
                indices_by_noun[noun] = []
            if desc:
                for part in desc.split():
                    if part not in groups[noun]["descs"]:
                        groups[noun]["descs"].append(part)
            indices_by_noun[noun].append(idx)

        if not groups:
            return tokens

        out_tokens: List[str] = []
        for idx, t in enumerate(tokens):
            replaced = False
            m = re.match(noun_pattern, t)
            if m:
                noun = m.group("noun")
                desc = m.group("desc").strip()
                if noun == "lipstick" and lip_gloss_present:
                    noun = "lip gloss"
                if groups.get(noun) and idx == groups[noun]["first_idx"]:
                    merged_desc = " ".join(groups[noun]["descs"]).strip()
                    merged = f"{merged_desc} {noun}".strip()
                    out_tokens.append(merged)
                    replaced = True
                else:
                    if noun in groups:
                        replaced = True
            if not replaced:
                out_tokens.append(t)
        return out_tokens

    norm_tokens = _merge_descriptor_groups(norm_tokens)

    mapped = _dedupe_near(norm_tokens, threshold=94)
    seen = set()
    out: List[str] = []
    for t in mapped:
        if t not in seen:
            out.append(t)
            seen.add(t)

    if cfg.sfw_mode:
        covered: List[str] = []
        for t in out:
            if t in {"nipples", "areolae", "erect nipples"}:
                covered.append("covered nipples")
            elif t == "penis":
                covered.append("covered penis")
            elif t == "anus":
                covered.append("covered anus")
            elif t == "pubic hair":
                covered.append("pubic hair peek")
            else:
                covered.append(t)
        out = covered

    original_count = len(tokens)
    min_keep = max(10, int(round(0.35 * original_count)))
    if len(out) < min_keep:
        have = set(out)
        for tok in tokens:
            if len(out) >= min_keep:
                break
            key = tok.lower().replace("_", " ")
            if key not in have:
                out.append(key)
                have.add(key)

    return ", ".join(out)


def consolidate_with_llm(*args, **kwargs):  # legacy symbol kept for safety
    text = args[0] if args else ""
    cfg = kwargs.get("cfg") or (args[1] if len(args) > 1 else None)
    if cfg is None:
        return text
    return consolidate_algorithmic(text, cfg)


def decide_automatic(*_args, **_kwargs) -> bool:  # legacy symbol kept for safety
    return False
