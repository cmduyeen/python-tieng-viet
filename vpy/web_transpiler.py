"""Bo dich hai chieu cho HTML/CSS tieng Viet (.vhtml/.vcss <-> .html/.css)."""

import re
from typing import Dict

from . import js_transpiler

TAG_MAP: Dict[str, str] = {
    "trang": "html",
    "dau": "head",
    "than": "body",
    "ten": "title",
    "kieu": "style",
    "tieude": "h1",
    "tieude1": "h1",
    "tieude2": "h2",
    "tieude3": "h3",
    "tieude4": "h4",
    "tieude5": "h5",
    "tieude6": "h6",
    "doan": "p",
    "hop": "div",
    "nut": "button",
    "hinh": "img",
    "lienket": "a",
    "danhsach": "ul",
    "danhsach_so": "ol",
    "muc": "li",
    "bang": "table",
    "hang": "tr",
    "o_bang": "td",
    "o_tieude": "th",
    "onhap": "input",
    "nhap_nhieu": "textarea",
    "nhan": "label",
    "bieumau": "form",
    "chu": "span",
    "chudam": "strong",
    "chunghieng": "em",
    "xuongdong": "br",
    "duongke": "hr",
    "kichban": "script",
    "lienket_file": "link",
    "thongtin": "meta",
}

REVERSE_TAG_MAP: Dict[str, str] = {v: k for k, v in TAG_MAP.items()}

ATTR_MAP: Dict[str, str] = {
    "lop": "class",
    "ma": "id",
    "nguon": "src",
    "diachi": "href",
    "mota": "alt",
    "loai": "type",
    "goiy": "placeholder",
    "file": "href",
    "lienket_kieu": "rel",
}

REVERSE_ATTR_MAP: Dict[str, str] = {v: k for k, v in ATTR_MAP.items()}

CSS_PROP_MAP: Dict[str, str] = {
    "mau-chu": "color",
    "mau-nen": "background-color",
    "co-chu": "font-size",
    "can-le": "text-align",
    "le-trong": "padding",
    "le-ngoai": "margin",
    "vien": "border",
    "bo-goc": "border-radius",
    "chieu-rong": "width",
    "chieu-cao": "height",
    "hien-thi": "display",
    "khoang-cach": "gap",
    "bong": "box-shadow",
    "phong-chu": "font-family",
    "do-dam": "font-weight",
    "con-tro": "cursor",
    "can-doc": "align-items",
    "can-ngang": "justify-content",
    "chuyen-dong": "transition",
}

REVERSE_CSS_PROP_MAP: Dict[str, str] = {v: k for k, v in CSS_PROP_MAP.items()}

CSS_VAL_MAP: Dict[str, str] = {
    "giua": "center",
    "trai": "left",
    "phai": "right",
    "ngang": "flex",
    "an": "none",
    "khoi": "block",
    "dam": "bold",
    "ban-tay": "pointer",
    # Mau sac tieng Viet
    "xanh-duong": "blue",
    "xanh-la": "green",
    "xanh-ngoc": "cyan",
    "xanh-nhat": "lightblue",
    "vang-nhat": "lightyellow",
    "xanh": "blue",
    "do": "red",
    "cam": "orange",
    "vang": "yellow",
    "tim": "purple",
    "hong": "pink",
    "trang": "white",
    "den": "black",
    "xam": "gray",
    "nau": "brown",
}

REVERSE_CSS_VAL_MAP: Dict[str, str] = {v: k for k, v in CSS_VAL_MAP.items()}
REVERSE_CSS_VAL_MAP["blue"] = "xanh-duong"


def transpile_vcss_to_css(source: str) -> str:
    """Chuyen CSS tieng Viet (.vcss) sang CSS chuan."""
    return _transform_css(source, CSS_PROP_MAP, CSS_VAL_MAP, TAG_MAP)


def transpile_css_to_vcss(source: str) -> str:
    """Chuyen CSS chuan sang CSS tieng Viet (.vcss)."""
    return _transform_css(source, REVERSE_CSS_PROP_MAP, REVERSE_CSS_VAL_MAP, REVERSE_TAG_MAP)


def _transform_css(
    source: str,
    prop_map: Dict[str, str],
    val_map: Dict[str, str],
    selector_map: Dict[str, str],
) -> str:
    def _sel_repl(m: re.Match[str]) -> str:
        prefix, tag_name, rest = m.group(1), m.group(2), m.group(3)
        new_tag = selector_map.get(tag_name.lower(), tag_name)
        return f"{prefix}{new_tag}{rest}"

    out = re.sub(r"(^|[\s,}])([a-zA-Z][a-zA-Z0-9-]*)(\s*\{)", _sel_repl, source, flags=re.MULTILINE)

    def _prop_repl(m: re.Match[str]) -> str:
        prefix, prop, val = m.group(1), m.group(2), m.group(3)
        new_prop = prop_map.get(prop.lower(), prop)
        new_val = val
        for k in sorted(val_map.keys(), key=len, reverse=True):
            v = val_map[k]
            new_val = re.sub(rf"(?<![a-zA-Z0-9-]){re.escape(k)}(?![a-zA-Z0-9-])", v, new_val)
        return f"{prefix}{new_prop}:{new_val}"

    return re.sub(r"(^|[{;\s])([a-zA-Z-]+)\s*:([^;{}\n]+)", _prop_repl, out, flags=re.MULTILINE)


def transpile_vhtml_to_html(source: str) -> str:
    """Chuyen HTML tieng Viet (.vhtml) sang HTML chuan (kem dich <kieu> -> <style>, <kichban> -> <script>)."""
    # Ho tro the lien ket CSS nhanh: <lienket_css file="style.css"> -> <link rel="stylesheet" href="style.css">
    out = re.sub(
        r'<lienket_css\s+(?:file|diachi)\s*=\s*(["\'][^"\']+["\'])\s*/?>',
        r'<link rel="stylesheet" href=\1>',
        source,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r'<lienket_js\s+(?:file|nguon)\s*=\s*(["\'][^"\']+["\'])\s*(?:/>|>\s*</lienket_js>)?',
        r'<script src=\1></script>',
        out,
        flags=re.IGNORECASE,
    )
    out = _transform_html_tags(out, TAG_MAP, ATTR_MAP)
    out = re.sub(
        r"(<style\b[^>]*>)([\s\S]*?)(</style>)",
        lambda m: f"{m.group(1)}{transpile_vcss_to_css(m.group(2))}{m.group(3)}",
        out,
        flags=re.IGNORECASE,
    )
    return re.sub(
        r"(<script\b[^>]*>)([\s\S]*?)(</script>)",
        lambda m: f"{m.group(1)}{js_transpiler.transpile_vjs_to_js(m.group(2))}{m.group(3)}",
        out,
        flags=re.IGNORECASE,
    )


def transpile_html_to_vhtml(source: str) -> str:
    """Chuyen HTML chuan sang .vhtml tieng Viet."""
    out = re.sub(
        r"(<style\b[^>]*>)([\s\S]*?)(</style>)",
        lambda m: f"{m.group(1)}{transpile_css_to_vcss(m.group(2))}{m.group(3)}",
        source,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"(<script\b[^>]*>)([\s\S]*?)(</script>)",
        lambda m: f"{m.group(1)}{js_transpiler.transpile_js_to_vjs(m.group(2))}{m.group(3)}",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r'<link\b[^>]*\brel\s*=\s*["\']stylesheet["\'][^>]*\bhref\s*=\s*(["\'][^"\']+["\'])[^>]*>',
        r'<lienket_css file=\1>',
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r'<script\b[^>]*\bsrc\s*=\s*(["\'][^"\']+["\'])[^>]*>\s*</script>',
        r'<lienket_js file=\1>',
        out,
        flags=re.IGNORECASE,
    )
    return _transform_html_tags(out, REVERSE_TAG_MAP, REVERSE_ATTR_MAP)


def _transform_html_tags(source: str, tag_map: Dict[str, str], attr_map: Dict[str, str]) -> str:
    def _tag_repl(m: re.Match[str]) -> str:
        slash, tag_name, attrs, self_close = m.group(1), m.group(2), m.group(3), m.group(4)
        new_tag = tag_map.get(tag_name.lower(), tag_name)
        new_attrs = attrs
        if attrs and not slash:
            for k, v in attr_map.items():
                new_attrs = re.sub(rf"(\s){re.escape(k)}(\s*=)", rf"\1{v}\2", new_attrs)
        return f"<{slash}{new_tag}{new_attrs}{self_close}>"

    return re.sub(r"<(/?)([a-zA-Z][a-zA-Z0-9_-]*)([^<>]*?)(/?)>", _tag_repl, source)


def ensure_html_document(html_fragment: str) -> str:
    """Boc doan HTML ngan thanh tai lieu HTML5 UTF-8 hoan chinh de mo trinh duyet."""
    if "<html" in html_fragment.lower():
        if "charset=" not in html_fragment.lower() and "<head" in html_fragment.lower():
            return re.sub(
                r"(<head\b[^>]*>)",
                r'\1\n    <meta charset="utf-8">',
                html_fragment,
                count=1,
                flags=re.IGNORECASE,
            )
        return html_fragment
    return (
        "<!DOCTYPE html>\n"
        '<html lang="vi">\n'
        "<head>\n"
        '    <meta charset="utf-8">\n'
        "    <title>Trang web vpy IDE</title>\n"
        "</head>\n"
        "<body>\n"
        f"{html_fragment}\n"
        "</body>\n"
        "</html>\n"
    )
