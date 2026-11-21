"""Dich cac loi Python pho bien (Traceback) sang tieng Viet cho nguoi moi."""

import re
import tokenize
from typing import Optional, Tuple

from . import ui


def explain_transpile_error(exc: Exception) -> Tuple[str, str, Optional[int]]:
    """Dich loi TokenError/IndentationError khi phan tich file .vpy."""
    if isinstance(exc, tokenize.TokenError):
        msg_raw = str(exc)
        m = re.search(r"\((\d+),\s*\d+\)", msg_raw)
        line_num = int(m.group(1)) if m else None
        line_info = f" (o dong {line_num})" if line_num else ""
        if "multi-line string" in msg_raw:
            return (
                f"Loi chua dong dau nhay{line_info}: Ban mo dau nhay \" hoac ' nhung quen dong lai.",
                "Goi y: Kiem tra lai cac chuoi van ban xem da co du cap dau nhay chua.",
                line_num,
            )
        return (
            f"Loi chua dong dau ngoac{line_info}: Co the ban mo '(' hoac '[' nhung quen dong lai.",
            "Goi y: Dem lai so dau ngoac mo va ngoac dong o dong nay.",
            line_num,
        )

    if isinstance(exc, IndentationError):
        line_num = getattr(exc, "lineno", None)
        line_info = f" (o dong {line_num})" if line_num else ""
        return (
            f"Loi thut le{line_info}: Khoang trang dau dong khong deu nhau.",
            "Goi y: Cac dong cung mot khoi lenh can thut le bang nhau (thuong la 4 dau cach).",
            line_num,
        )

    return f"Loi cu phap .vpy: {exc}", "", None


def explain_python_error(stderr_text: str) -> Tuple[str, str, Optional[int]]:
    """Tra ve (thong_bao_loi_chinh, goi_y, so_dong) tu stderr cua Python."""
    if not stderr_text.strip():
        return "", "", None

    line_num = _extract_user_line_number(stderr_text)
    line_info = f" (o dong {line_num})" if line_num else ""

    if "SyntaxError:" in stderr_text:
        return (
            f"Loi cu phap{line_info}: Ban viet sai quy tac cau lenh Python.",
            "Goi y: Kiem tra xem co thieu dau ':' o cuoi dong if/for/def, hoac thieu dau ngoac ')', dau nhay '\"' khong.",
            line_num,
        )
    if "IndentationError:" in stderr_text:
        return (
            f"Loi thut le{line_info}: Khoang trang dau dong khong deu nhau.",
            "Goi y: Trong Python, cac dong cung mot khoi phai thut le bang nhau (thuong la 4 dau cach).",
            line_num,
        )
    if "ModuleNotFoundError:" in stderr_text:
        mod = _extract_after(stderr_text, r"No module named '([^']+)'")
        hint = f"Goi y: Hay cai thu vien nay bang lenh: vpy cai {mod}" if mod else ""
        return f"Thieu thu vien '{mod or '?'}'{line_info}.", hint, line_num
    if "NameError:" in stderr_text:
        name = _extract_after(stderr_text, r"name '([^']+)' is not defined")
        return (
            f"Chua khai bao ten '{name or '?'}'{line_info}.",
            "Goi y: Kiem tra lai xem ban co go nham ten bien/ten ham, hoac quen dat chu trong dau ngoac kep \"...\" khong.",
            line_num,
        )
    if "TypeError:" in stderr_text:
        return (
            f"Loi sai kieu du lieu{line_info}: Vi du cong chu voi so, hoac truyen sai so luong tham so cho ham.",
            "",
            line_num,
        )
    if "ValueError:" in stderr_text:
        return (
            f"Loi gia tri khong hop le{line_info}: Vi du chuyen chu 'abc' thanh so nguyen.",
            "",
            line_num,
        )
    if "ZeroDivisionError:" in stderr_text:
        return (
            f"Loi chia cho 0{line_info}: Khong the chia mot so cho 0 duoc.",
            "",
            line_num,
        )
    if "IndexError:" in stderr_text:
        return (
            f"Loi vuot qua do dai danh sach{line_info}: Ban dang truy cap vi tri khong ton tai trong list.",
            "",
            line_num,
        )
    if "KeyError:" in stderr_text:
        return f"Khong tim thay khoa (key) trong tu dien (dict){line_info}.", "", line_num
    if "FileNotFoundError:" in stderr_text:
        return f"Khong tim thay file duoc mo trong code{line_info}.", "", line_num
    if "UnicodeEncodeError:" in stderr_text or "UnicodeDecodeError:" in stderr_text:
        return (
            f"Loi bang ma ky tu (UTF-8){line_info}: Chuong trinh gap ky tu tieng Viet khong tuong thich.",
            "Goi y: Hay chay bang 'vpy chay' hoac 'vpy ide' de tu dong bat che do UTF-8.",
            line_num,
        )

    return f"Chuong trinh gap loi{line_info}:", "", line_num


def translate_python_error(stderr_text: str) -> None:
    """Phan tich stderr tu Python va in giai thich tieng Viet ra terminal."""
    if not stderr_text.strip():
        return

    msg, hint, _ = explain_python_error(stderr_text)
    ui.error(msg)
    if hint:
        ui.info(hint)
    print()
    print(stderr_text)


def _extract_user_line_number(text: str) -> Optional[int]:
    """Lay so dong trong file cua nguoi dung, bo qua file thu vien he thong."""
    frames = re.findall(r'File "([^"]+)", line (\d+)', text)
    user_lines = [
        int(line)
        for path, line in frames
        if "encodings\\" not in path and "\\Lib\\" not in path and "/lib/python" not in path
    ]
    if user_lines:
        return user_lines[-1]

    matches = re.findall(r"line (\d+)", text)
    return int(matches[-1]) if matches else None


def _extract_after(text: str, pattern: str) -> str:
    m = re.search(pattern, text)
    return m.group(1) if m else ""
