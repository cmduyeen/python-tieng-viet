# vpy — Vietnamese Python for Beginners & Kids

[Tiếng Việt](README.md) · [English](README.en.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/cmduyeen)

`vpy` provides two layers for Vietnamese beginners learning Python:
1. **Vietnamese CLI commands:** Run files (`vpy chay`), auto-create virtual environments (`vpy tao_moitruong`), install packages (`vpy cai`), and **translate Python Tracebacks into Vietnamese**.
2. **Vietnamese Python syntax (`.vpy`) & built-in `vide` editor:** Write Python using Vietnamese keywords (`neu`, `nguoclai`, `voi ... trong dayso(...)`, `ham`, `in(...)`) and run directly or transpile to **100% standard `.py`** for side-by-side learning or production use by indie makers.

> 🌐 **Try online in your browser (no install required):** **[cmduyeen.github.io/python-tieng-viet](https://cmduyeen.github.io/python-tieng-viet/)**

## Quick Local Install
```powershell
git clone https://github.com/cmduyeen/python-tieng-viet.git
cd python-tieng-viet
pip install -e .
```

## `vpy` Command Reference

| Command | Meaning | Standard Equivalent |
| :--- | :--- | :--- |
| `vpy chay <file.py\|.vpy>` | Run file (with Vietnamese error explanations) | `python <file>` |
| `vpy dich <file.vpy>` | Transpile `.vpy` to standard `.py` | — |
| `vpy tao_moitruong` | Create `.venv` (auto-used when running/installing) | `python -m venv .venv` |
| `vpy cai <package>` | Install Python package | `pip install <package>` |
| `vpy go <package>` | Uninstall Python package | `pip uninstall -y <package>` |
| `vpy thuvien` | List installed packages | `pip list` |
| `vpy donggoi` | Save installed packages | `pip freeze > requirements.txt` |
| `vide` | Launch the built-in Vietnamese Python IDE | — |

## Example `xin_chao.vpy`
```python
ham chao(ten):
    neu ten == "An":
        in("Chao ban An!")
    nguoclai:
        in("Xin chao", ten)

voi i trong dayso(3):
    chao("An")
```
Run with: `vpy chay xin_chao.vpy`

## Vietnamese CLI Ecosystem

| Tool | Description | Repository |
| :--- | :--- | :--- |
| **vpy** *(current)* | Vietnamese Python (`.vpy`) & `vide` editor | [cmduyeen/python-tieng-viet](https://github.com/cmduyeen/python-tieng-viet) |
| **vgit** | Vietnamese Git CLI for beginners | [cmduyeen/git-tieng-viet](https://github.com/cmduyeen/git-tieng-viet) |
| **vgh** | Vietnamese GitHub CLI (`gh`) | [cmduyeen/github-tieng-viet](https://github.com/cmduyeen/github-tieng-viet) |
| **vwt** | Vietnamese Windows Terminal / PowerShell commands | [cmduyeen/terminal-tieng-viet](https://github.com/cmduyeen/terminal-tieng-viet) |

---

Developed by [cmduyeen](https://github.com/cmduyeen) · ☕ [Buy me a coffee (Ko-fi)](https://ko-fi.com/cmduyeen)
