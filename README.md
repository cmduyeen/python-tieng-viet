# vpy — Python tiếng Việt cho người mới học & trẻ em

[Tiếng Việt](README.md) · [English](README.en.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/cmduyeen)

`vpy` hỗ trợ cả 2 tầng cho người Việt mới học Python:
1. **Lệnh CLI tiếng Việt:** Chạy file (`vpy chay`), tạo môi trường ảo tự động (`vpy tao_moitruong`), cài thư viện (`vpy cai`), và **dịch lỗi Traceback Python sang tiếng Việt**.
2. **Code Python tiếng Việt (`.vpy`):** Viết bằng từ khóa tiếng Việt (`neu`, `nguoclai`, `voi ... trong dayso(...)`, `ham`, `in(...)`) và chạy trực tiếp hoặc dịch sang `.py` chuẩn để học đối chiếu.

## Cài đặt thử nghiệm (Local)
```powershell
cd D:\Brain2nd\06-Code\vpy
pip install -e .
```

## Bảng lệnh `vpy`

| Lệnh `vpy` | Ý nghĩa | Lệnh gốc tương đương |
| :--- | :--- | :--- |
| `vpy chay <file.py\|.vpy>` | Chạy file (kèm dịch lỗi tiếng Việt) | `python <file>` |
| `vpy dich <file.vpy>` | Chuyển `.vpy` sang `.py` chuẩn | — |
| `vpy tao_moitruong` | Tạo `.venv` (tự động dùng khi chạy/cài) | `python -m venv .venv` |
| `vpy cai <thư-viện>` | Cài thư viện Python | `pip install <thư-viện>` |
| `vpy go <thư-viện>` | Gỡ thư viện Python | `pip uninstall -y <thư-viện>` |
| `vpy thuvien` | Xem thư viện đã cài | `pip list` |
| `vpy donggoi` | Lưu danh sách thư viện | `pip freeze > requirements.txt` |

## Ví dụ một file `xin_chao.vpy`
```python
ham chao(ten):
    neu ten == "An":
        in("Chao ban An!")
    nguoclai:
        in("Xin chao", ten)

voi i trong dayso(3):
    chao("An")
```
Chạy ngay bằng: `vpy chay xin_chao.vpy` (hoặc mở trình soạn thảo `vide` đi kèm).

## Bộ công cụ lập trình tiếng Việt

| Công cụ | Mô tả | Link |
| :--- | :--- | :--- |
| **vpy** *(đang xem)* | Python tiếng Việt (`.vpy`) & trình soạn thảo `vide` | [cmduyeen/vpy](https://github.com/cmduyeen/vpy) |
| **vgit** | Git tiếng Việt cho người mới học | [cmduyeen/vgit](https://github.com/cmduyeen/vgit) |
| **vgh** | GitHub CLI (`gh`) tiếng Việt | [cmduyeen/vgh](https://github.com/cmduyeen/vgh) |
| **vwt** | Windows Terminal / PowerShell tiếng Việt | [cmduyeen/vwt](https://github.com/cmduyeen/vwt) |

---

Phát triển bởi [cmduyeen](https://github.com/cmduyeen) · ☕ [Mời mình 1 ly cà phê (Ko-fi)](https://ko-fi.com/cmduyeen)
