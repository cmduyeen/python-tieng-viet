"""Tien ich giao dien terminal cho vpy."""

import os
import sys


def enable_windows_ansi() -> None:
    if os.name == "nt":
        os.system("")
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def paint(text: str, *styles: str) -> str:
    if not _supports_color() or not styles:
        return text
    return f"{''.join(styles)}{text}{Color.RESET}"


def info(msg: str) -> None:
    print(paint(f"[vpy] {msg}", Color.CYAN))


def success(msg: str) -> None:
    print(paint(f"[OK] {msg}", Color.GREEN, Color.BOLD))


def warn(msg: str) -> None:
    print(paint(f"[!] {msg}", Color.YELLOW))


def error(msg: str) -> None:
    print(paint(f"[Loi] {msg}", Color.RED, Color.BOLD), file=sys.stderr)


def show_bridge(py_cmd: str, enabled: bool = True) -> None:
    if enabled and py_cmd:
        print(paint(f"  -> Lenh Python goc: {py_cmd}", Color.GRAY))


def ask_text(prompt: str) -> str:
    try:
        return input(paint(f"? {prompt}: ", Color.YELLOW, Color.BOLD)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""
