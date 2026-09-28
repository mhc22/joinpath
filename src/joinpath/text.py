from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9_]+|[\u4e00-\u9fff]+", re.I)
_CJK = re.compile(r"^[\u4e00-\u9fff]+$")

STOP = {
    "the",
    "a",
    "an",
    "of",
    "for",
    "and",
    "or",
    "in",
    "on",
    "to",
    "from",
    "with",
    "by",
    "is",
    "的",
    "了",
    "吗",
    "呢",
    "啊",
    "吧",
    "我",
    "我们",
    "一下",
    "多少",
    "什么",
    "怎么",
    "如何",
    "请",
    "帮我",
    "查询",
    "看看",
    "统计",
}


def tokenize(text: str) -> list[str]:
    parts = _TOKEN.findall(text.lower())
    out: list[str] = []
    for part in parts:
        if part in STOP:
            continue
        if _CJK.match(part):
            if len(part) >= 2:
                out.append(part)
            out.extend(part[i : i + 2] for i in range(len(part) - 1) if part[i : i + 2] not in STOP)
            out.extend(ch for ch in part if ch not in STOP)
        else:
            out.append(part)
    return out


def phrase_in(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    return needle.lower() in haystack.lower()
