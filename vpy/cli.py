"""Entry point cho lenh `vpy`."""

import subprocess
import sys
from typing import List, Optional

from . import __version__, commands, ui


def main(argv: Optional[List[str]] = None) -> int:
    ui.enable_windows_ansi()
    args = sys.argv[1:] if argv is None else argv

    if not args:
        return commands.cmd_huongdan([])

    if args[0] in ("-v", "--version", "phienban"):
        print(f"vpy phien ban {__version__}")
        return 0

    cmd_name = args[0].lower()
    rest = args[1:]

    handler = commands.COMMAND_MAP.get(cmd_name)
    if handler is not None:
        return handler(rest)

    # Pass-through: chay truc tiep bang python goc
    proc = subprocess.run([commands.get_active_python(), *args])
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
