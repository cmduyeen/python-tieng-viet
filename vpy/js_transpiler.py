"""Bo dich hai chieu giua JavaScript tieng Viet (.vjs) va JavaScript chuan (.js)."""

import re
from typing import Dict

JS_KEYWORD_MAP: Dict[str, str] = {
    "bien": "let",
    "hangso": "const",
    "ham": "function",
    "trave": "return",
    "neu": "if",
    "nguoclai": "else",
    "trongkhi": "while",
    "voi": "for",
    "dunglai": "break",
    "tieptuc": "continue",
    "Dung": "true",
    "Sai": "false",
    "Rong": "null",
    "ghilog": "console.log",
    "thongbao": "alert",
    "hoinho": "prompt",
    "xacnhan": "confirm",
    "tim_the": "document.querySelector",
    "tim_tatca": "document.querySelectorAll",
    "tim_ma": "document.getElementById",
}

REVERSE_JS_KEYWORD_MAP: Dict[str, str] = {v: k for k, v in JS_KEYWORD_MAP.items()}

JS_PROP_MAP: Dict[str, str] = {
    "noidung": "textContent",
    "ma_html": "innerHTML",
    "giatri": "value",
    "langnghe": "addEventListener",
    "dodai": "length",
}

REVERSE_JS_PROP_MAP: Dict[str, str] = {v: k for k, v in JS_PROP_MAP.items()}

_TOKEN_RE = re.compile(
    r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`|//[^\n]*|/\*[\s\S]*?\*/)',
)


def transpile_vjs_to_js(source: str) -> str:
    """Chuyen JavaScript tieng Viet (.vjs) sang JavaScript chuan (.js)."""
    out = _replace_code_segments(source, JS_KEYWORD_MAP, JS_PROP_MAP)
    return re.sub(r"\bhoacla\b", "else if", out)


def transpile_js_to_vjs(source: str) -> str:
    """Chuyen JavaScript chuan (.js) sang .vjs tieng Viet."""
    out = re.sub(r"\belse\s+if\b", "hoacla", source)
    return _replace_code_segments(out, REVERSE_JS_KEYWORD_MAP, REVERSE_JS_PROP_MAP)


def _replace_code_segments(source: str, kw_map: Dict[str, str], prop_map: Dict[str, str]) -> str:
    parts = _TOKEN_RE.split(source)
    result = []
    # Sap xep key dai truoc (vd: document.querySelector truoc cac key ngan)
    sorted_kws = sorted(kw_map.keys(), key=len, reverse=True)
    sorted_props = sorted(prop_map.keys(), key=len, reverse=True)

    for idx, part in enumerate(parts):
        # Cac phan tu le la chuoi hoac comment -> giu nguyen
        if idx % 2 == 1:
            result.append(part)
            continue

        seg = part
        for k in sorted_kws:
            v = kw_map[k]
            seg = re.sub(rf"(?<![A-Za-z0-9_.]){re.escape(k)}(?![A-Za-z0-9_])", v, seg)
        for pk in sorted_props:
            pv = prop_map[pk]
            seg = re.sub(rf"\.{re.escape(pk)}(?![A-Za-z0-9_])", f".{pv}", seg)
        result.append(seg)

    return "".join(result)
