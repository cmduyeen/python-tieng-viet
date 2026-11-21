"""Bo phan tich ngu canh va goi y thong minh (IntelliSense) cho vpy IDE."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .snippets import (
    COLOR_COMPLETIONS_VI,
    COMPLETIONS_CSS,
    COMPLETIONS_HTML,
    COMPLETIONS_HTML_ATTRS,
    COMPLETIONS_JS,
    COMPLETIONS_PY,
    COMPLETIONS_VCSS,
    COMPLETIONS_VHTML,
    COMPLETIONS_VHTML_ATTRS,
    COMPLETIONS_VJS,
    COMPLETIONS_VPY,
    MEMBER_COMPLETIONS,
)


def detect_code_mode(text: str, file_path: Optional[Path] = None) -> str:
    """Tu dong nhan dien loai code dua vao duoi file hoac noi dung dang go."""
    if file_path is not None:
        ext = file_path.suffix.lower()
        if ext in (".vpy", ".py", ".vhtml", ".html", ".vcss", ".css", ".vjs", ".js"):
            return ext

    stripped = text.strip()
    if not stripped:
        return ".vpy"

    # 1. Nhan dien Web (HTML / VHTML)
    if re.search(
        r"<(?:trang|dau|than|ten|kieu|kichban|tieude\d*|doan|hop|nut|hinh|lienket|lienket_css|lienket_js|danhsach|muc|onhap|bang|hang|o_bang)\b",
        stripped,
        re.IGNORECASE,
    ):
        return ".vhtml"
    if re.search(r"<!doctype|<html\b|<head\b|<body\b|<h[1-6]\b|<div\b|<p\b|<button\b|<img\b|<a\b|<script\b", stripped, re.IGNORECASE):
        return ".html"

    # 2. Nhan dien JavaScript (.vjs / .js)
    if re.search(r"\b(?:bien|hangso)\s+[A-Za-z_]\w*\s*=|\b(?:ghilog|thongbao|tim_ma|tim_the)\s*\(|\bham\s+[A-Za-z_]\w*\s*\([^)]*\)\s*\{", stripped):
        return ".vjs"
    if re.search(r"\b(?:let|const|var)\s+[A-Za-z_]\w*\s*=|\b(?:console\.log|alert|document\.querySelector|document\.getElementById)\s*\(|\bfunction\s+[A-Za-z_]\w*\s*\(", stripped):
        return ".js"

    # 3. Nhan dien CSS / VCSS
    if "{" in stripped and ":" in stripped and not re.search(r"^\s*(?:ham|def|neu|if|voi|for|bien|let|const|function)\b", stripped, re.MULTILINE):
        if re.search(r"\b(?:mau-chu|mau-nen|co-chu|can-le|le-trong|le-ngoai|bo-goc|vien|chieu-rong|chieu-cao)\s*:", stripped):
            return ".vcss"
        if re.search(r"\b(?:color|background-color|font-size|text-align|padding|margin|border-radius|display)\s*:", stripped):
            return ".css"

    # 3. Nhan dien Python goc vs Python Viet
    has_en_py = bool(re.search(r"\b(?:def|print|input|import|elif|range|True|False|None)\b", stripped))
    has_vi_py = bool(re.search(r"\b(?:ham|nhap|neu|hoacla|nguoclai|voi|trongkhi|dayso|Dung|Sai|Rong|dung)\b|\bin\s*\(", stripped))
    if has_en_py and not has_vi_py:
        return ".py"

    return ".vpy"


def is_in_string_or_comment(line_prefix: str) -> bool:
    """Kiem tra con tro co dang nam trong chuoi hay comment khong."""
    in_single = False
    in_double = False
    escaped = False
    for ch in line_prefix:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return True
    return in_single or in_double


def extract_user_symbols(text: str) -> Tuple[List[Tuple[str, str, str]], Dict[str, str]]:
    """Trich xuat bien, ham, thu vien nguoi dung vua viet trong code."""
    items: List[Tuple[str, str, str]] = []
    seen: set[str] = set()
    obj_types: Dict[str, str] = {}

    for m in re.finditer(r"^\s*(?:ham|def)\s+([A-Za-z_]\w*)\s*\(([^)]*)\)", text, re.MULTILINE):
        fn_name, params = m.group(1), m.group(2).strip()
        if fn_name not in seen:
            seen.add(fn_name)
            snip = f"{fn_name}($0)" if params else f"{fn_name}()$0"
            items.append((fn_name, snip, f"[Ham] {fn_name}({params})"))

    for m in re.finditer(r"^\s*(?:dung|import)\s+([A-Za-z_]\w*)", text, re.MULTILINE):
        mod = m.group(1)
        if mod not in seen:
            seen.add(mod)
            items.append((mod, f"{mod}$0", "[Thu vien]"))

    for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+)$", text, re.MULTILINE):
        var_name, rhs = m.group(1), m.group(2).strip()
        if "turtle.Turtle" in rhs:
            obj_types[var_name] = "turtle_obj"
        if var_name not in seen:
            seen.add(var_name)
            items.append((var_name, f"{var_name}$0", "[Bien]"))

    for m in re.finditer(r"^\s*(?:voi|for)\s+([A-Za-z_]\w*)\s+(?:trong|in)\b", text, re.MULTILINE):
        var_name = m.group(1)
        if var_name not in seen:
            seen.add(var_name)
            items.append((var_name, f"{var_name}$0", "[Bien lap]"))

    return items, obj_types


def fuzzy_score(query: str, candidate: str, has_snippet: bool = False) -> Optional[int]:
    """Cham diem khop: 0=khop chinh xac co snippet, 1=bat dau bang, 2=chuoi con, 3=fuzzy."""
    q = query.lower()
    c = candidate.lower()
    if c == q:
        return 0 if has_snippet else None
    if c.startswith(q):
        return 1
    if q in c:
        return 2
    it = iter(c)
    if all(ch in it for ch in q):
        return 3
    return None


def _detect_web_subcontext(text_before_cursor: str, mode: str) -> str:
    """Nhan dien ngu canh con trong HTML/VHTML: 'vcss', 'css', 'vhtml_attr', 'html_attr', hoac mode goc."""
    low = text_before_cursor.lower()
    if mode == ".vhtml":
        last_open_style = low.rfind("<kieu")
        last_close_style = low.rfind("</kieu>")
        if last_open_style > last_close_style:
            return ".vcss"
        last_open_js = low.rfind("<kichban")
        last_close_js = low.rfind("</kichban>")
        if last_open_js > last_close_js:
            return ".vjs"
        if low.rfind("<") > low.rfind(">") and " " in low[low.rfind("<"):]:
            return "vhtml_attr"
    elif mode == ".html":
        last_open_style = low.rfind("<style")
        last_close_style = low.rfind("</style>")
        if last_open_style > last_close_style:
            return ".css"
        last_open_js = low.rfind("<script")
        last_close_js = low.rfind("</script>")
        if last_open_js > last_close_js:
            return ".js"
        if low.rfind("<") > low.rfind(">") and " " in low[low.rfind("<"):]:
            return "html_attr"
    return mode


def get_completions(
    full_text: str,
    line_prefix: str,
    mode: str,
    force: bool = False,
    text_before_cursor: str = "",
) -> Tuple[List[Tuple[str, str, str]], int]:
    """Tra ve (danh_sach_goi_y, cot_bat_dau_tu)."""
    if is_in_string_or_comment(line_prefix):
        return [], 0

    user_items, obj_types = extract_user_symbols(full_text)

    if mode in (".vpy", ".py"):
        dot_match = re.search(r"([A-Za-z_]\w*)\.([A-Za-z0-9_]*)$", line_prefix)
        if dot_match:
            obj_name, member_prefix = dot_match.group(1), dot_match.group(2)
            kind = obj_types.get(obj_name, obj_name)
            candidates = MEMBER_COMPLETIONS.get(kind, MEMBER_COMPLETIONS["common_var"])
            if member_prefix:
                scored = []
                for item in candidates:
                    sc = fuzzy_score(member_prefix, item[0], has_snippet=True)
                    if sc is not None:
                        scored.append((sc, len(item[0]), item))
                scored.sort(key=lambda x: (x[0], x[1]))
                matches = [x[2] for x in scored]
            else:
                matches = list(candidates)
            return matches[:8], len(line_prefix) - len(member_prefix)

    m = re.search(r"([A-Za-z_!][A-Za-z0-9_-]*)$", line_prefix)
    prefix = m.group(1) if m else ""
    has_open_angle = False
    if mode in (".vhtml", ".html"):
        m_tag = re.search(r"<([A-Za-z0-9_-]*)$", line_prefix)
        if m_tag:
            prefix = m_tag.group(1)
            has_open_angle = True

    if not force and not has_open_angle and len(prefix) < 1:
        return [], 0

    effective_ctx = _detect_web_subcontext(text_before_cursor, mode) if mode in (".vhtml", ".html") else mode
    # Goi y ten mau tieng Viet khi dang go gia tri sau mau-chu: / mau-nen:
    if effective_ctx == ".vcss" and re.search(r"(?:mau-chu|mau-nen)\s*:\s*[a-zA-Z-]*$", line_prefix):
        full_pool = list(COLOR_COMPLETIONS_VI)
        word_col = len(line_prefix) - len(prefix)
        if not prefix:
            return full_pool[:8], word_col
        scored = []
        for item in full_pool:
            sc = fuzzy_score(prefix, item[0], has_snippet=True)
            if sc is not None:
                scored.append((sc, len(item[0]), item))
        scored.sort(key=lambda x: (x[0], x[1]))
        return [x[2] for x in scored][:8], word_col

    mode_pools = {
        ".vpy": COMPLETIONS_VPY,
        ".py": COMPLETIONS_PY,
        ".vhtml": COMPLETIONS_VHTML,
        ".html": COMPLETIONS_HTML,
        ".vcss": COMPLETIONS_VCSS,
        ".css": COMPLETIONS_CSS,
        ".vjs": COMPLETIONS_VJS,
        ".js": COMPLETIONS_JS,
        "vhtml_attr": COMPLETIONS_VHTML_ATTRS,
        "html_attr": COMPLETIONS_HTML_ATTRS,
    }
    base_pool = mode_pools.get(effective_ctx, COMPLETIONS_VPY)
    if effective_ctx in (".vpy", ".py"):
        existing_names = {item[0] for item in user_items}
        full_pool = user_items + [c for c in base_pool if c[0] not in existing_names]
    else:
        full_pool = list(base_pool)

    word_col = len(line_prefix) - len(prefix) - (1 if has_open_angle else 0)

    if not prefix:
        return full_pool[:8], word_col

    scored = []
    for item in full_pool:
        has_snip = item[1].replace("$0", "") != item[0]
        sc = fuzzy_score(prefix, item[0], has_snippet=has_snip)
        if sc is not None:
            scored.append((sc, len(item[0]), item))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in scored][:8], word_col
