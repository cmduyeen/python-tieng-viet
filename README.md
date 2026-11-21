# 🐍 python-tieng-viet (`vpy` & `vide`) — Học Python bằng tiếng Việt

[Tiếng Việt](README.md) · [English](README.en.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/cmduyeen)

Học lập trình Python dễ dàng ngay từ ngày đầu tiên mà không bị rào cản tiếng Anh. Viết code bằng từ khóa tiếng Việt (`.vpy`), chạy lệnh tiếng Việt trên terminal (`vpy`), và mở trình soạn thảo có sẵn (`vide`).

> 🌐 **Dùng thử ngay trên trình duyệt (không cần cài đặt):** **[cmduyeen.github.io/python-tieng-viet](https://cmduyeen.github.io/python-tieng-viet/)**

## 🎯 Dành cho ai?

- **Người mới bắt đầu & Trẻ em:** Làm quen tư duy lập trình bằng tiếng Việt tự nhiên, không bị ngợp bởi từ khóa hay thông báo lỗi tiếng Anh.
- **Người làm độc lập (Indie / Maker):** Viết nhanh ý tưởng bằng `.vpy` rồi dùng `vpy dich` (hoặc Web Studio) để **chuyển sang code Python `.py` chuẩn 100% đúng định dạng**, chạy thật ở mọi môi trường làm việc.

## ✨ Điểm nổi bật

- **Dễ hiểu từ dòng đầu tiên:** Viết logic bằng từ khóa quen thuộc (`neu`, `nguoclai`, `voi ... trong dayso(...)`, `ham`, `in(...)`) — cực kỳ hợp cho học sinh, trẻ em và người mới bắt đầu.
- **Dịch lỗi Traceback sang tiếng Việt:** Khi code sai, `vpy` giải thích lỗi rõ ràng bằng tiếng Việt để bạn biết sai ở đâu và sửa thế nào, không còn hoảng sợ trước màn hình lỗi đỏ tiếng Anh.
- **Tự động học sang Python chuẩn:** Dùng `vpy dich <file.vpy>` để chuyển đổi sang file `.py` chuẩn quốc tế, giúp bạn vừa làm vừa đối chiếu.
- **Đi kèm sẵn IDE `vide` & không cần cài thư viện ngoài:** Chỉ cài 1 gói duy nhất là có cả CLI `vpy` lẫn trình soạn thảo `vide` có gợi ý code.

---

## ⚡ Bắt đầu trong 30 giây

### 1. Cài đặt

```powershell
git clone https://github.com/cmduyeen/python-tieng-viet.git
cd python-tieng-viet
pip install -e .
```

### 2. Thực hành bài đầu tiên (`xin_chao.vpy`)

Tạo file `xin_chao.vpy` với nội dung:

```python
ham chao(ten):
    neu ten == "An":
        in("Chào bạn An!")
    nguoclai:
        in("Xin chào", ten)

voi i trong dayso(3):
    chao("An")
```

Chạy ngay trên terminal:

```powershell
vpy chay xin_chao.vpy
```

Hoặc gõ `vide` để mở trình soạn thảo trực quan:

```powershell
vide
```

> 💡 **Mẹo thực hành trọn bộ bằng tiếng Việt:** Dùng [`vwt` (terminal-tieng-viet)](https://github.com/cmduyeen/terminal-tieng-viet) để tạo/vào thư mục học (`taothumuc`, `vao`), rồi dùng [`vgit` (git-tieng-viet)](https://github.com/cmduyeen/git-tieng-viet) và [`vgh` (github-tieng-viet)](https://github.com/cmduyeen/github-tieng-viet) để lưu bài tập lên GitHub (`vgit luu`, `vgh taorepo`).

---

## 📖 Bảng lệnh `vpy`

| Lệnh `vpy` | Công dụng | Lệnh Python gốc tương đương |
| :--- | :--- | :--- |
| `vpy chay <file.py\|.vpy>` | Chạy file (kèm dịch lỗi tiếng Việt) | `python <file>` |
| `vpy dich <file.vpy>` | Chuyển `.vpy` sang `.py` chuẩn | — |
| `vpy tao_moitruong` | Tạo môi trường ảo `.venv` tự động | `python -m venv .venv` |
| `vpy cai <thư-viện>` | Cài đặt thư viện Python | `pip install <thư-viện>` |
| `vpy go <thư-viện>` | Gỡ thư viện Python | `pip uninstall -y <thư-viện>` |
| `vpy thuvien` | Xem danh sách thư viện đã cài | `pip list` |
| `vpy donggoi` | Lưu danh sách thư viện ra `requirements.txt` | `pip freeze > requirements.txt` |
| `vide` | Mở trình soạn thảo Python tiếng Việt | — |

---

## 🧰 Bộ công cụ lập trình tiếng Việt

| Công cụ | Mô tả | Link |
| :--- | :--- | :--- |
| **python-tieng-viet** *(đang xem)* | Python tiếng Việt (`vpy`) & trình soạn thảo `vide` | [cmduyeen/python-tieng-viet](https://github.com/cmduyeen/python-tieng-viet) |
| **git-tieng-viet** | Git tiếng Việt (`vgit`) cho người mới học | [cmduyeen/git-tieng-viet](https://github.com/cmduyeen/git-tieng-viet) |
| **github-tieng-viet** | GitHub CLI tiếng Việt (`vgh`) | [cmduyeen/github-tieng-viet](https://github.com/cmduyeen/github-tieng-viet) |
| **terminal-tieng-viet** | Windows Terminal / PowerShell tiếng Việt (`vwt`) | [cmduyeen/terminal-tieng-viet](https://github.com/cmduyeen/terminal-tieng-viet) |

---

[MIT License](LICENSE) · Phát triển bởi [cmduyeen](https://github.com/cmduyeen) · ☕ [Mời mình 1 ly cà phê (Ko-fi)](https://ko-fi.com/cmduyeen)
