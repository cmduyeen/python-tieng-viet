"""Cac lenh Viet hoa cho Python (vpy)."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, List

from . import config, error_translator, transpiler, ui


def _bridge_enabled() -> bool:
    return bool(config.load_config().get("bridge_mode", True))


def get_active_python() -> str:
    """Tu dong dung .venv o thu muc hien tai neu co, khong can activate thu cong."""
    cwd = Path.cwd()
    candidates = [
        cwd / ".venv" / "Scripts" / "python.exe",
        cwd / ".venv" / "bin" / "python",
        cwd / "venv" / "Scripts" / "python.exe",
        cwd / "venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return sys.executable


def cmd_chay(args: List[str]) -> int:
    """Chay file .py hoac .vpy (co dich loi Python sang tieng Viet)."""
    if not args:
        target = ui.ask_text("Nhap ten file Python can chay (vd: main.py hoac bai1.vpy)")
        if not target:
            ui.error("Chua co ten file de chay.")
            return 1
        args = [target]

    target_path = Path(args[0])
    extra_args = args[1:]

    if not target_path.exists():
        ui.error(f"Khong tim thay file '{target_path}'.")
        ui.info("Goi y: Kiem tra lai ten file hoac go 'lietke' / 'dir' de xem cac file dang co.")
        return 1

    py_exe = get_active_python()
    temp_file: Path | None = None
    run_path = target_path

    if target_path.suffix.lower() == ".vpy":
        try:
            src = target_path.read_text(encoding="utf-8")
            py_code = transpiler.transpile_vpy_to_py(src)
        except Exception as exc:
            msg, hint, _ = error_translator.explain_transpile_error(exc)
            ui.error(msg)
            if hint:
                ui.info(hint)
            return 1

        fd, tmp_name = tempfile.mkstemp(suffix=".py", prefix="vpy_")
        os.close(fd)
        temp_file = Path(tmp_name)
        temp_file.write_text(py_code, encoding="utf-8")
        run_path = temp_file

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        interactive_tty = sys.stdin.isatty() and sys.stdout.isatty()
        proc = subprocess.run(
            [py_exe, str(run_path), *extra_args],
            stdout=None if interactive_tty else subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if not interactive_tty and proc.stdout:
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")

        if proc.returncode != 0:
            error_translator.translate_python_error(proc.stderr)
            return proc.returncode

        if target_path.suffix.lower() == ".vpy":
            ui.show_bridge(f"python {target_path.with_suffix('.py').name}", _bridge_enabled())
        else:
            ui.show_bridge(f"python {target_path.name}", _bridge_enabled())
        return 0
    finally:
        if temp_file and temp_file.exists():
            temp_file.unlink(missing_ok=True)


def cmd_dich(args: List[str]) -> int:
    """Dich file .vpy (tieng Viet) sang file .py chuan de hoc va doi chieu."""
    if not args:
        src_name = ui.ask_text("Nhap ten file .vpy muon dich sang .py")
        if not src_name:
            return 1
        args = [src_name]

    src_path = Path(args[0])
    if not src_path.exists():
        ui.error(f"Khong tim thay file '{src_path}'.")
        return 1

    out_path = Path(args[1]) if len(args) > 1 else src_path.with_suffix(".py")
    py_code = transpiler.transpile_vpy_to_py(src_path.read_text(encoding="utf-8"))
    out_path.write_text(py_code, encoding="utf-8")

    ui.success(f"Da dich '{src_path.name}' -> '{out_path.name}'!")
    return 0


def cmd_tao_moitruong(args: List[str]) -> int:
    """Tao moi truong ao rieng cho du an (.venv)."""
    env_name = args[0] if args else ".venv"
    if Path(env_name).exists():
        ui.warn(f"Moi truong '{env_name}' da ton tai roi.")
        return 0

    ui.info(f"Dang tao moi truong ao '{env_name}'...")
    proc = subprocess.run([sys.executable, "-m", "venv", env_name])
    if proc.returncode != 0:
        ui.error("Khong tao duoc moi truong ao.")
        return proc.returncode

    ui.success(f"Da tao moi truong ao '{env_name}'! Tu nay 'vpy cai' va 'vpy chay' se tu dong dung moi truong nay.")
    ui.show_bridge(f"python -m venv {env_name}", _bridge_enabled())
    return 0


def cmd_cai(args: List[str]) -> int:
    """Cai dat thu vien Python (pip install)."""
    if not args:
        pkg = ui.ask_text("Nhap ten thu vien muon cai (vd: requests, pygame)")
        if not pkg:
            return 1
        args = [pkg]

    py_exe = get_active_python()
    ui.info(f"Dang cai dat thu vien: {' '.join(args)}...")
    proc = subprocess.run([py_exe, "-m", "pip", "install", *args])
    if proc.returncode == 0:
        ui.success("Cai dat thu vien thanh cong!")
        ui.show_bridge(f"pip install {' '.join(args)}", _bridge_enabled())
    else:
        ui.error("Cai dat thu vien that bai. Kiem tra lai ten thu vien hoac mang Internet.")
    return proc.returncode


def cmd_go(args: List[str]) -> int:
    """Go bo thu vien Python (pip uninstall)."""
    if not args:
        pkg = ui.ask_text("Nhap ten thu vien muon go bo")
        if not pkg:
            return 1
        args = [pkg]

    py_exe = get_active_python()
    proc = subprocess.run([py_exe, "-m", "pip", "uninstall", "-y", *args])
    if proc.returncode == 0:
        ui.success(f"Da go bo: {' '.join(args)}")
        ui.show_bridge(f"pip uninstall -y {' '.join(args)}", _bridge_enabled())
    return proc.returncode


def cmd_thuvien(args: List[str]) -> int:
    """Xem danh sach thu vien da cai (pip list)."""
    py_exe = get_active_python()
    proc = subprocess.run([py_exe, "-m", "pip", "list", *args])
    if proc.returncode == 0:
        ui.show_bridge("pip list", _bridge_enabled())
    return proc.returncode


def cmd_donggoi(args: List[str]) -> int:
    """Luu danh sach thu vien ra file requirements.txt (pip freeze)."""
    out_file = Path(args[0]) if args else Path("requirements.txt")
    py_exe = get_active_python()
    proc = subprocess.run(
        [py_exe, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        ui.error("Khong lay duoc danh sach thu vien.")
        return proc.returncode

    out_file.write_text(proc.stdout, encoding="utf-8")
    ui.success(f"Da luu danh sach thu vien vao '{out_file}'.")
    ui.show_bridge(f"pip freeze > {out_file}", _bridge_enabled())
    return 0


def cmd_caidat(args: List[str]) -> int:
    """Bat/tat che do Cau noi."""
    cfg = config.load_config()
    if not args:
        state = "BAT" if cfg.get("bridge_mode", True) else "TAT"
        print(f"Che do Cau noi (hien lenh Python goc): {state}")
        print("Cach doi: 'vpy caidat bridge bat' hoac 'vpy caidat bridge tat'")
        return 0

    if args[0].lower() == "bridge" and len(args) >= 2:
        val = args[1].lower() in ("bat", "on", "true", "1", "co")
        cfg["bridge_mode"] = val
        config.save_config(cfg)
        ui.success(f"Da {'BAT' if val else 'TAT'} che do Cau noi.")
        return 0
    return 1


def cmd_ide(args: List[str]) -> int:
    """Mo trinh soan thao mini vpy IDE (viet code .py/.vpy va bao loi tieng Viet)."""
    from . import ide

    target = args[0] if args else None
    return ide.launch_ide(initial_file=target)


def cmd_huongdan(args: List[str]) -> int:
    """Hien thi bang lenh vpy va tu khoa .vpy."""
    print(ui.paint("=== vpy - Python tieng Viet cho nguoi moi ===", ui.Color.CYAN, ui.Color.BOLD))
    rows = [
        ("vpy ide [file]", "Mo cua so IDE viet code va bao loi tieng Viet"),
        ("vpy chay <file.py|.vpy>", "Chay chuong trinh va dich loi sang tieng Viet"),
        ("vpy dich <file.vpy>", "Chuyen code tieng Viet (.vpy) sang file .py chuan"),
        ("vpy tao_moitruong", "Tao moi truong ao .venv (tu dong dung khi chay/cai)"),
        ("vpy cai <thu-vien>", "Cai thu vien Python (pip install)"),
        ("vpy go <thu-vien>", "Go bo thu vien (pip uninstall)"),
        ("vpy thuvien", "Xem danh sach thu vien da cai (pip list)"),
        ("vpy donggoi", "Luu danh sach thu vien ra requirements.txt"),
        ("vpy caidat", "Bat/tat che do hien lenh Python goc"),
    ]
    for cmd, desc in rows:
        print(f"  {ui.paint(cmd.ljust(26), ui.Color.GREEN)} {desc}")
    print()
    print(ui.paint("Tu khoa trong file .vpy:", ui.Color.YELLOW, ui.Color.BOLD))
    print("  in(...) -> print(...)      | nhap(...) -> input(...)   | ham -> def")
    print("  neu / hoacla / nguoclai    | voi x trong dayso(5):     | trongkhi -> while")
    print("  Dung / Sai / Rong          | va / hoac / khong         | trave -> return")
    return 0


COMMAND_MAP: Dict[str, Callable[[List[str]], int]] = {
    "ide": cmd_ide,
    "chay": cmd_chay,
    "dich": cmd_dich,
    "tao_moitruong": cmd_tao_moitruong,
    "moitruong": cmd_tao_moitruong,
    "cai": cmd_cai,
    "go": cmd_go,
    "thuvien": cmd_thuvien,
    "donggoi": cmd_donggoi,
    "caidat": cmd_caidat,
    "huongdan": cmd_huongdan,
    "help": cmd_huongdan,
    "-h": cmd_huongdan,
    "--help": cmd_huongdan,
}
