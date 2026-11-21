"""Bo dich hai chieu giua Python tieng Viet (.vpy) va Python chuan (.py) bang tokenize."""

import io
import tokenize
from typing import Dict, List

KEYWORD_MAP: Dict[str, str] = {
    # Dieu khien luong
    "neu": "if",
    "hoacla": "elif",
    "nguoclai": "else",
    "voi": "for",
    "trong": "in",
    "trongkhi": "while",
    "dunglai": "break",
    "tieptuc": "continue",
    "boqua": "pass",
    # Ham & Lop
    "ham": "def",
    "trave": "return",
    "lop": "class",
    # Ngoai le
    "thu": "try",
    "batloi": "except",
    "cuoicung": "finally",
    # Import
    "dung": "import",
    "tu": "from",
    "la": "as",
    # Logic & Hang so
    "va": "and",
    "hoac": "or",
    "khong": "not",
    "Dung": "True",
    "Sai": "False",
    "Rong": "None",
    # Ham co ban
    "nhap": "input",
    "dodai": "len",
    "dayso": "range",
    "songuyen": "int",
    "sothuc": "float",
    "chuoi": "str",
    "danhsach": "list",
    "tudien": "dict",
    "taphop": "set",
    "tinhtong": "sum",
    "lonnhat": "max",
    "nhonhat": "min",
    "sapxep": "sorted",
    "lamtron": "round",
    "tuyetdoi": "abs",
    "giatrituyetdoi": "abs",
    "kieu": "type",
    "mofile": "open",
    "luythua": "pow",
    "tatca": "all",
    "batky": "any",
}

REVERSE_KEYWORD_MAP: Dict[str, str] = {v: k for k, v in KEYWORD_MAP.items()}
REVERSE_KEYWORD_MAP["print"] = "in"
REVERSE_KEYWORD_MAP["abs"] = "tuyetdoi"


def transpile_vpy_to_py(source: str) -> str:
    """Chuyen ma nguon .vpy sang ma nguon Python chuan, giu nguyen chuoi va comment."""
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    out_tokens: List[tokenize.TokenInfo] = []

    for i, tok in enumerate(tokens):
        if tok.type == tokenize.NAME:
            prev_is_def = i > 0 and tokens[i - 1].type == tokenize.NAME and tokens[i - 1].string in ("ham", "def")
            prev_is_attr = i > 0 and tokens[i - 1].string == "."
            if prev_is_def or prev_is_attr:
                out_tokens.append(tok)
                continue
            # Truong hop dac biet: `in(...)` la ham print, con `trong` da la `in`
            if tok.string == "in" and i + 1 < len(tokens) and tokens[i + 1].string == "(":
                tok = tok._replace(string="print")
            elif tok.string in KEYWORD_MAP:
                tok = tok._replace(string=KEYWORD_MAP[tok.string])
        out_tokens.append(tok)

    return tokenize.untokenize(out_tokens)


def transpile_py_to_vpy(source: str) -> str:
    """Chuyen ma nguon Python chuan (.py) sang .vpy tieng Viet, giu nguyen chuoi va comment."""
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    out_tokens: List[tokenize.TokenInfo] = []

    for i, tok in enumerate(tokens):
        if tok.type == tokenize.NAME:
            prev_is_def = i > 0 and tokens[i - 1].type == tokenize.NAME and tokens[i - 1].string in ("ham", "def")
            prev_is_attr = i > 0 and tokens[i - 1].string == "."
            if prev_is_def or prev_is_attr:
                out_tokens.append(tok)
                continue
            if tok.string in REVERSE_KEYWORD_MAP:
                tok = tok._replace(string=REVERSE_KEYWORD_MAP[tok.string])
        out_tokens.append(tok)

    return tokenize.untokenize(out_tokens)
