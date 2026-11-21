"""IDE mini bo cuc kieu VS Code (Explorer + Tabs + Editor + Console + Status Bar)."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from typing import Dict, List, Optional, Tuple

from . import error_translator, intellisense, js_transpiler, snippets, transpiler, web_transpiler

BG_WARM = "#f7eed6"
BG_SIDEBAR = "#efe3c4"
BG_TAB_BAR = "#e5d5b5"
BG_TAB_ACTIVE = "#fffdf7"
BG_EDITOR = "#fffdf7"
BG_GUTTER = "#efe3c4"
BG_CONSOLE = "#1f1916"
BG_STATUS = "#5c4332"
FG_CONSOLE = "#f7eed6"
FG_DARK = "#2c1e16"
ACCENT_GREEN = "#2e6f28"
ACCENT_RED = "#b91c1c"
ACCENT_GOLD = "#92400e"
ERR_LINE_BG = "#fee2e2"


@dataclass
class TabState:
    title: str
    path: Optional[Path]
    content: str
    mode: str
    modified: bool = False


class VPyIDE:
    def __init__(self, root: tk.Tk, initial_target: Optional[str] = None) -> None:
        self.root = root
        self.root.title("vide - Hoc code co ban bang tieng Viet")
        self.root.geometry("1120x720")
        self.root.configure(bg=BG_WARM)

        self.workspace_dir: Optional[Path] = None
        self._explorer_items: List[Tuple[str, Path]] = []

        self._tabs: List[TabState] = []
        self._active_tab_idx: int = -1

        self.mode_var = tk.StringVar(value=".vpy")
        self._active_mode = ".vpy"
        self.font_size = 12
        self.running_proc: Optional[subprocess.Popen[str]] = None
        self._stderr_chunks: list[str] = []

        self._ac_popup: Optional[tk.Toplevel] = None
        self._ac_listbox: Optional[tk.Listbox] = None
        self._ac_matches: List[Tuple[str, str, str]] = []
        self._ac_word_start: str = "1.0"
        self._diag_after_id: Optional[str] = None
        self._live_server: Optional[ThreadingHTTPServer] = None
        self._live_port: Optional[int] = None
        self._live_root: Optional[Path] = None
        self._live_version: int = 1
        self._last_html_tab_idx: Optional[int] = None

        self._build_toolbar()
        self._build_status_bar()
        self._build_main_layout()
        self._bind_shortcuts()

        target_path = Path(initial_target).resolve() if initial_target else None
        if target_path and target_path.is_dir():
            self.workspace_dir = target_path
            self.refresh_explorer()
            self.new_file()
        elif target_path and target_path.is_file():
            self.workspace_dir = target_path.parent
            self.refresh_explorer()
            self.load_file(target_path)
        else:
            self.refresh_explorer()
            self.new_file()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    @property
    def current_file(self) -> Optional[Path]:
        if 0 <= self._active_tab_idx < len(self._tabs):
            return self._tabs[self._active_tab_idx].path
        return None

    @current_file.setter
    def current_file(self, value: Optional[Path]) -> None:
        if 0 <= self._active_tab_idx < len(self._tabs):
            self._tabs[self._active_tab_idx].path = value
            if value is not None:
                self._tabs[self._active_tab_idx].title = value.name

    def _build_toolbar(self) -> None:
        bar1 = tk.Frame(self.root, bg=BG_WARM, padx=10, pady=7)
        bar1.pack(fill=tk.X)

        btn_cfg = {
            "relief": tk.FLAT,
            "padx": 9,
            "pady": 4,
            "font": ("Segoe UI", 9, "bold"),
            "cursor": "hand2",
        }

        tk.Button(bar1, text="Moi", bg="#e5d5b5", fg=FG_DARK, command=self.new_file, **btn_cfg).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(bar1, text="Mo file", bg="#e5d5b5", fg=FG_DARK, command=self.open_file, **btn_cfg).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(bar1, text="Mo thu muc", bg="#e5d5b5", fg=FG_DARK, command=self.open_folder, **btn_cfg).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(bar1, text="Luu", bg="#e5d5b5", fg=FG_DARK, command=self.save_file, **btn_cfg).pack(side=tk.LEFT, padx=(0, 12))

        self.run_btn = tk.Button(bar1, text="Chay (F5)", bg=ACCENT_GREEN, fg="white", command=self.run_code, **btn_cfg)
        self.run_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.stop_btn = tk.Button(bar1, text="Dung", bg=ACCENT_RED, fg="white", command=self.stop_code, state=tk.DISABLED, **btn_cfg)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 12))

        self.convert_btn = tk.Button(bar1, text="Sang code goc", bg=ACCENT_GOLD, fg="white", command=self.toggle_convert_mode, **btn_cfg)
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(bar1, text="Dep code", bg="#d9c39e", fg=FG_DARK, command=self.format_code, **btn_cfg).pack(side=tk.LEFT, padx=(0, 6))

        lesson_menu_btn = tk.Menubutton(bar1, text="Bai mau", bg="#d9c39e", fg=FG_DARK, **btn_cfg)
        lesson_menu = tk.Menu(lesson_menu_btn, tearoff=0)
        py_lessons = [n for n, (ext, _) in snippets.LESSONS.items() if ext == ".vpy"]
        web_lessons = [n for n, (ext, _) in snippets.LESSONS.items() if ext == ".vhtml"]
        for name in py_lessons:
            lesson_menu.add_command(label=f"[Python] {name}", command=lambda n=name: self._load_lesson(n))
        if web_lessons:
            lesson_menu.add_separator()
            for name in web_lessons:
                lesson_menu.add_command(label=f"[Web] {name}", command=lambda n=name: self._load_lesson(n))
        lesson_menu_btn.config(menu=lesson_menu)
        lesson_menu_btn.pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(bar1, text="Tu dien", bg="#d9c39e", fg=FG_DARK, command=self.show_dictionary, **btn_cfg).pack(side=tk.LEFT)

        tk.Button(bar1, text="A+", bg="#e5d5b5", fg=FG_DARK, command=lambda: self._change_font(1), **btn_cfg).pack(side=tk.RIGHT, padx=(4, 0))
        tk.Button(bar1, text="A-", bg="#e5d5b5", fg=FG_DARK, command=lambda: self._change_font(-1), **btn_cfg).pack(side=tk.RIGHT)

    def _build_status_bar(self) -> None:
        status = tk.Frame(self.root, bg=BG_STATUS, padx=10, pady=3)
        status.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_left = tk.Label(status, text="San sang", bg=BG_STATUS, fg="#f7eed6", font=("Segoe UI", 9))
        self.status_left.pack(side=tk.LEFT)

        self.status_right = tk.Label(status, text="Dong 1, Cot 1  |  .vpy", bg=BG_STATUS, fg="#f7eed6", font=("Segoe UI", 9))
        self.status_right.pack(side=tk.RIGHT)

    def _build_main_layout(self) -> None:
        outer = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=BG_WARM, sashwidth=5)
        outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

        # --- Sidebar Explorer ben trai ---
        sidebar = tk.Frame(outer, bg=BG_SIDEBAR, width=220, bd=1, relief=tk.SOLID)
        sb_head = tk.Frame(sidebar, bg="#dfcda7", padx=6, pady=4)
        sb_head.pack(fill=tk.X)
        self.explorer_title = tk.Label(sb_head, text="THU MUC", bg="#dfcda7", fg=FG_DARK, font=("Segoe UI", 9, "bold"), anchor=tk.W)
        self.explorer_title.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(sb_head, text="+", bg="#d2bc90", fg=FG_DARK, relief=tk.FLAT, padx=5, command=self._create_file_in_explorer, cursor="hand2").pack(side=tk.RIGHT, padx=(2, 0))
        tk.Button(sb_head, text="R", bg="#d2bc90", fg=FG_DARK, relief=tk.FLAT, padx=5, command=self.refresh_explorer, cursor="hand2").pack(side=tk.RIGHT)

        self.explorer_list = tk.Listbox(
            sidebar,
            bg=BG_SIDEBAR,
            fg=FG_DARK,
            selectbackground=ACCENT_GREEN,
            selectforeground="white",
            border=0,
            highlightthickness=0,
            font=("Segoe UI", 10),
        )
        self.explorer_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.explorer_list.bind("<Double-Button-1>", self._on_explorer_activate)
        self.explorer_list.bind("<Return>", self._on_explorer_activate)
        outer.add(sidebar, width=220)

        # --- Vung ben phai: Tabs + Editor + Console ---
        right_pane = tk.PanedWindow(outer, orient=tk.VERTICAL, bg=BG_WARM, sashwidth=6)
        outer.add(right_pane)

        editor_container = tk.Frame(right_pane, bg=BG_EDITOR, bd=1, relief=tk.SOLID)
        self.tab_bar = tk.Frame(editor_container, bg=BG_TAB_BAR)
        self.tab_bar.pack(fill=tk.X)

        editor_frame = tk.Frame(editor_container, bg=BG_EDITOR)
        editor_frame.pack(fill=tk.BOTH, expand=True)

        self.gutter = tk.Text(
            editor_frame,
            width=4,
            padx=6,
            pady=8,
            takefocus=0,
            border=0,
            bg=BG_GUTTER,
            fg="#6b4f3b",
            state=tk.DISABLED,
            font=("Consolas", self.font_size),
        )
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)

        scroll_y = tk.Scrollbar(editor_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x = tk.Scrollbar(editor_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.editor = tk.Text(
            editor_frame,
            wrap=tk.NONE,
            undo=True,
            padx=8,
            pady=8,
            border=0,
            bg=BG_EDITOR,
            fg=FG_DARK,
            insertbackground=FG_DARK,
            font=("Consolas", self.font_size),
            yscrollcommand=self._sync_scroll_set(scroll_y),
            xscrollcommand=scroll_x.set,
        )
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.config(command=self._sync_scroll_yview)
        scroll_x.config(command=self.editor.xview)

        self.editor.tag_configure("kw", foreground="#9a3412", font=("Consolas", self.font_size, "bold"))
        self.editor.tag_configure("builtin", foreground="#1d4ed8")
        self.editor.tag_configure("fn", foreground="#7e22ce", font=("Consolas", self.font_size, "bold"))
        self.editor.tag_configure("num", foreground="#c2410c")
        self.editor.tag_configure("attr", foreground="#0369a1")
        self.editor.tag_configure("str", foreground="#15803d")
        self.editor.tag_configure("cmt", foreground="#78716c", font=("Consolas", self.font_size, "italic"))
        self.editor.tag_configure("err_line", background=ERR_LINE_BG)
        self.editor.tag_configure("lint_err", underline=True, foreground="#dc2626")
        self.editor.tag_configure("brace_match", background="#fde68a", font=("Consolas", self.font_size, "bold"))
        self.editor.tag_configure("find_match", background="#fed7aa")
        self.editor.tag_raise("str")
        self.editor.tag_raise("cmt")
        self.editor.tag_raise("lint_err")

        # Thanh tim kiem nhanh (Ctrl+F), an mac dinh
        self.find_bar = tk.Frame(editor_container, bg="#efe3c4", padx=8, pady=4)
        tk.Label(self.find_bar, text="Tim:", bg="#efe3c4", fg=FG_DARK, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.find_entry = tk.Entry(self.find_bar, bg="white", fg=FG_DARK, relief=tk.FLAT, font=("Consolas", 10), width=24)
        self.find_entry.pack(side=tk.LEFT, padx=(0, 6))
        self.find_entry.bind("<Return>", lambda _e: self.find_next())
        self.find_entry.bind("<Escape>", lambda _e: self.hide_find_bar())
        tk.Button(self.find_bar, text="Tim tiep", bg="#d9c39e", fg=FG_DARK, relief=tk.FLAT, padx=8, command=self.find_next, cursor="hand2").pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(self.find_bar, text="Dong", bg="#d9c39e", fg=FG_DARK, relief=tk.FLAT, padx=6, command=self.hide_find_bar, cursor="hand2").pack(side=tk.RIGHT)

        right_pane.add(editor_container, height=420)

        # --- Console & Thanh nhap lieu ---
        console_frame = tk.Frame(right_pane, bg=BG_CONSOLE)
        tk.Label(
            console_frame,
            text="Ket qua chay chuong trinh & Giai thich loi tieng Viet:",
            bg="#2c221e",
            fg="#eab308",
            anchor=tk.W,
            padx=8,
            pady=4,
            font=("Segoe UI", 9, "bold"),
        ).pack(fill=tk.X)

        input_bar = tk.Frame(console_frame, bg="#2c221e", padx=8, pady=6)
        input_bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(input_bar, text="Nhap du lieu (cho lenh nhap):", bg="#2c221e", fg="#f7eed6", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.stdin_entry = tk.Entry(input_bar, bg="#3b2f2a", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT, font=("Consolas", 11), state=tk.DISABLED, disabledbackground="#2c221e")
        self.stdin_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.stdin_entry.bind("<Return>", lambda _e: self.send_stdin())
        self.send_btn = tk.Button(input_bar, text="Gui", bg=ACCENT_GREEN, fg="white", relief=tk.FLAT, padx=12, command=self.send_stdin, cursor="hand2", state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT)

        self.console = tk.Text(
            console_frame,
            wrap=tk.WORD,
            padx=10,
            pady=8,
            border=0,
            bg=BG_CONSOLE,
            fg=FG_CONSOLE,
            state=tk.DISABLED,
            font=("Consolas", 11),
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        self.console.tag_configure("err", foreground="#fca5a5", font=("Consolas", 11, "bold"))
        self.console.tag_configure("hint", foreground="#fde047")
        self.console.tag_configure("ok", foreground="#86efac")
        self.console.tag_configure("raw", foreground="#a8a29e")
        self.console.tag_configure("inp", foreground="#93c5fd")

        right_pane.add(console_frame, height=220)

    # --- Explorer ---

    def refresh_explorer(self) -> None:
        self.explorer_list.delete(0, tk.END)
        self._explorer_items = []

        if self.workspace_dir is None:
            self.explorer_title.config(text="THU MUC: (Chua mo)")
            return

        self.explorer_title.config(text=f"THU MUC: {self.workspace_dir.name or str(self.workspace_dir)}")
        parent = self.workspace_dir.parent
        if parent != self.workspace_dir:
            self._explorer_items.append(("dir", parent))
            self.explorer_list.insert(tk.END, "[..] Quay lai")

        try:
            entries = sorted(self.workspace_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            entries = []

        for entry in entries:
            if entry.name.startswith(".") or entry.name == "__pycache__":
                continue
            if entry.is_dir():
                self._explorer_items.append(("dir", entry))
                self.explorer_list.insert(tk.END, f"[Thu muc] {entry.name}")
            elif entry.suffix.lower() in (".vpy", ".py", ".vhtml", ".html", ".vcss", ".css", ".vjs", ".js", ".txt", ".md"):
                self._explorer_items.append(("file", entry))
                self.explorer_list.insert(tk.END, f"  {entry.name}")

    def open_folder(self) -> None:
        start_dir = str(self.workspace_dir) if self.workspace_dir else str(Path.home())
        folder = filedialog.askdirectory(initialdir=start_dir)
        if folder:
            self.workspace_dir = Path(folder)
            self.refresh_explorer()

    def _on_explorer_activate(self, _event=None) -> None:
        sel = self.explorer_list.curselection()
        if not sel or sel[0] >= len(self._explorer_items):
            return
        kind, path = self._explorer_items[sel[0]]
        if kind == "dir":
            self.workspace_dir = path
            self.refresh_explorer()
        else:
            self.load_file(path)

    def _create_file_in_explorer(self) -> None:
        if self.workspace_dir is None:
            self.open_folder()
            if self.workspace_dir is None:
                return
        name = simpledialog.askstring("Tao file moi", "Nhap ten file (vd: bai2.vpy):", parent=self.root)
        if not name:
            return
        if "." not in name:
            name += self.mode_var.get()
        target = self.workspace_dir / name
        if not target.exists():
            target.write_text("", encoding="utf-8")
        self.refresh_explorer()
        self.load_file(target)

    # --- Quan ly Tabs ---

    def _save_active_tab_state(self) -> None:
        if 0 <= self._active_tab_idx < len(self._tabs):
            tab = self._tabs[self._active_tab_idx]
            tab.content = self.editor.get("1.0", "end-1c")
            tab.mode = self._active_mode
            tab.modified = self.editor.edit_modified()

    def _render_tab_bar(self) -> None:
        for w in self.tab_bar.winfo_children():
            w.destroy()
        for idx, tab in enumerate(self._tabs):
            is_active = idx == self._active_tab_idx
            bg = BG_TAB_ACTIVE if is_active else BG_TAB_BAR
            frame = tk.Frame(self.tab_bar, bg=bg, bd=1, relief=tk.RAISED if is_active else tk.FLAT)
            frame.pack(side=tk.LEFT, padx=(2, 0), pady=(3, 0))

            label_text = f"{'* ' if tab.modified else ''}{tab.title}"
            btn = tk.Button(
                frame,
                text=label_text,
                bg=bg,
                fg=FG_DARK,
                relief=tk.FLAT,
                padx=8,
                pady=3,
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                command=lambda i=idx: self.switch_tab(i),
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT)

            close_btn = tk.Button(
                frame,
                text="x",
                bg=bg,
                fg="#78716c",
                relief=tk.FLAT,
                padx=4,
                pady=3,
                font=("Segoe UI", 8, "bold"),
                command=lambda i=idx: self.close_tab(i),
                cursor="hand2",
            )
            close_btn.pack(side=tk.LEFT)

    def _open_or_create_tab(self, title: str, path: Optional[Path], content: str, mode: str, modified: bool = False) -> None:
        if path is not None:
            for idx, tab in enumerate(self._tabs):
                if tab.path is not None and tab.path.resolve() == path.resolve():
                    self.switch_tab(idx)
                    return

        self._save_active_tab_state()
        new_tab = TabState(title=title, path=path, content=content, mode=mode, modified=modified)
        self._tabs.append(new_tab)
        self._active_tab_idx = len(self._tabs) - 1
        self._apply_tab_to_editor(new_tab)

    def switch_tab(self, idx: int) -> None:
        if idx == self._active_tab_idx or not (0 <= idx < len(self._tabs)):
            return
        self._save_active_tab_state()
        self._active_tab_idx = idx
        self._apply_tab_to_editor(self._tabs[idx])

    def close_tab(self, idx: int) -> None:
        if not (0 <= idx < len(self._tabs)):
            return
        self._save_active_tab_state()
        tab = self._tabs[idx]
        if tab.modified:
            ans = messagebox.askyesnocancel("Chua luu bai", f"'{tab.title}' co thay doi chua luu. Luu truoc khi dong?")
            if ans is None:
                return
            if ans is True:
                self.switch_tab(idx)
                if not self.save_file():
                    return

        self._tabs.pop(idx)
        if not self._tabs:
            self._active_tab_idx = -1
            self._open_or_create_tab("Chua luu.vpy", None, "", ".vpy", modified=False)
            return

        new_idx = min(idx, len(self._tabs) - 1)
        self._active_tab_idx = new_idx
        self._apply_tab_to_editor(self._tabs[new_idx])

    def _sync_family_lang_from_mode(self, mode: str) -> None:
        if hasattr(self, "convert_btn"):
            is_vi = mode in (".vpy", ".vhtml", ".vcss", ".vjs")
            self.convert_btn.config(text="Sang code goc" if is_vi else "Ve code Viet")

    def _apply_tab_to_editor(self, tab: TabState) -> None:
        self.mode_var.set(tab.mode)
        self._sync_family_lang_from_mode(tab.mode)
        self._active_mode = tab.mode
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", tab.content)
        self.editor.edit_modified(tab.modified)
        self.root.title(f"vpy IDE - {tab.title}")
        self._render_tab_bar()
        self._on_editor_change()

    # --- Sync Scroll & Shortcuts ---

    def _sync_scroll_set(self, scrollbar: tk.Scrollbar):
        def _setter(first: str, last: str) -> None:
            scrollbar.set(first, last)
            self.gutter.yview_moveto(first)
        return _setter

    def _sync_scroll_yview(self, *args) -> None:
        self.editor.yview(*args)
        self.gutter.yview(*args)

    def _bind_shortcuts(self) -> None:
        self.editor.bind("<KeyPress>", self._on_key_press)
        self.editor.bind("<KeyRelease>", self._on_key_release)
        self.editor.bind("<ButtonRelease-1>", lambda _e: (self._update_status_bar(), self._highlight_matching_brace()))
        self.editor.bind("<Tab>", self._on_tab)
        self.editor.bind("<Shift-Tab>", self._on_shift_tab)
        self.editor.bind("<Return>", self._on_return)
        self.editor.bind("<BackSpace>", self._on_backspace)
        self.editor.bind("<Up>", self._on_up_down)
        self.editor.bind("<Down>", self._on_up_down)
        self.editor.bind("<Escape>", lambda _e: (self._hide_autocomplete(), self.hide_find_bar()))
        self.editor.bind("<FocusOut>", lambda _e: self._hide_autocomplete())
        self.editor.bind("<Control-space>", lambda _e: self._trigger_autocomplete())
        self.editor.bind("<Control-slash>", lambda _e: self.toggle_comment())
        self.editor.bind("<Control-f>", lambda _e: self.show_find_bar())
        self.editor.bind("<Control-Shift-F>", lambda _e: self.format_code())
        self.root.bind("<F5>", lambda _e: self.run_code())
        self.root.bind("<Control-s>", lambda _e: self.save_file())
        self.root.bind("<Control-o>", lambda _e: self.open_file())
        self.root.bind("<Control-n>", lambda _e: self.new_file())

    def _on_key_press(self, event: tk.Event) -> Optional[str]:
        ch = event.char
        if not ch:
            return None

        if ch in (")", "]", "}", '"', "'"):
            next_ch = self.editor.get(tk.INSERT, f"{tk.INSERT}+1c")
            if next_ch == ch:
                self.editor.mark_set(tk.INSERT, f"{tk.INSERT}+1c")
                return "break"

        if ch in snippets.PAIR_CHARS:
            close_ch = snippets.PAIR_CHARS[ch]
            try:
                sel_start = self.editor.index(tk.SEL_FIRST)
                sel_end = self.editor.index(tk.SEL_LAST)
                selected = self.editor.get(sel_start, sel_end)
                self.editor.delete(sel_start, sel_end)
                self.editor.insert(sel_start, f"{ch}{selected}{close_ch}")
                self.editor.mark_set(tk.INSERT, f"{sel_start}+{len(selected) + 1}c")
            except tk.TclError:
                pos = self.editor.index(tk.INSERT)
                self.editor.insert(pos, f"{ch}{close_ch}")
                self.editor.mark_set(tk.INSERT, f"{pos}+1c")
            self._on_editor_change()
            return "break"
        return None

    def _on_backspace(self, _event: tk.Event) -> Optional[str]:
        prev_ch = self.editor.get(f"{tk.INSERT}-1c", tk.INSERT)
        next_ch = self.editor.get(tk.INSERT, f"{tk.INSERT}+1c")
        if prev_ch in snippets.PAIR_CHARS and snippets.PAIR_CHARS[prev_ch] == next_ch:
            self.editor.delete(f"{tk.INSERT}-1c", f"{tk.INSERT}+1c")
            self._on_editor_change()
            return "break"
        return None

    def _on_tab(self, _event: tk.Event) -> str:
        if self._ac_popup is not None:
            self._accept_autocomplete()
            return "break"
        try:
            sel_start = self.editor.index(tk.SEL_FIRST)
            sel_end = self.editor.index(tk.SEL_LAST)
            start_line = int(sel_start.split(".")[0])
            end_line = int(sel_end.split(".")[0])
            if sel_end.endswith(".0") and end_line > start_line:
                end_line -= 1
            if end_line > start_line:
                for ln in range(start_line, end_line + 1):
                    self.editor.insert(f"{ln}.0", "    ")
                self._on_editor_change()
                return "break"
            self.editor.delete(sel_start, sel_end)
        except tk.TclError:
            pass
        self.editor.insert(tk.INSERT, "    ")
        self._on_editor_change()
        return "break"

    def _on_shift_tab(self, _event: Optional[tk.Event] = None) -> str:
        try:
            start_line = int(self.editor.index(tk.SEL_FIRST).split(".")[0])
            sel_end = self.editor.index(tk.SEL_LAST)
            end_line = int(sel_end.split(".")[0])
            if sel_end.endswith(".0") and end_line > start_line:
                end_line -= 1
        except tk.TclError:
            start_line = end_line = int(self.editor.index(tk.INSERT).split(".")[0])

        for ln in range(start_line, end_line + 1):
            line_text = self.editor.get(f"{ln}.0", f"{ln}.4")
            spaces = len(line_text) - len(line_text.lstrip(" "))
            if spaces > 0:
                self.editor.delete(f"{ln}.0", f"{ln}.{spaces}")
        self._on_editor_change()
        return "break"

    def toggle_comment(self) -> str:
        """Bat/tat comment (# cho Python, <!-- --> cho HTML) cho dong hoac khoi dang chon."""
        try:
            start_line = int(self.editor.index(tk.SEL_FIRST).split(".")[0])
            sel_end = self.editor.index(tk.SEL_LAST)
            end_line = int(sel_end.split(".")[0])
            if sel_end.endswith(".0") and end_line > start_line:
                end_line -= 1
        except tk.TclError:
            start_line = end_line = int(self.editor.index(tk.INSERT).split(".")[0])

        is_web = self.mode_var.get() in (".vhtml", ".html")
        if is_web:
            for ln in range(start_line, end_line + 1):
                line_text = self.editor.get(f"{ln}.0", f"{ln}.end")
                stripped = line_text.strip()
                if stripped.startswith("<!--") and stripped.endswith("-->"):
                    inner = stripped[4:-3].strip()
                    indent = line_text[: len(line_text) - len(line_text.lstrip())]
                    self.editor.delete(f"{ln}.0", f"{ln}.end")
                    self.editor.insert(f"{ln}.0", f"{indent}{inner}")
                elif stripped:
                    indent = line_text[: len(line_text) - len(line_text.lstrip())]
                    self.editor.delete(f"{ln}.0", f"{ln}.end")
                    self.editor.insert(f"{ln}.0", f"{indent}<!-- {stripped} -->")
        else:
            lines = [self.editor.get(f"{ln}.0", f"{ln}.end") for ln in range(start_line, end_line + 1)]
            all_commented = all(not l.strip() or l.lstrip().startswith("#") for l in lines)
            for ln in range(start_line, end_line + 1):
                line_text = self.editor.get(f"{ln}.0", f"{ln}.end")
                if not line_text.strip():
                    continue
                indent_len = len(line_text) - len(line_text.lstrip())
                if all_commented:
                    after = line_text[indent_len:]
                    if after.startswith("# "):
                        self.editor.delete(f"{ln}.{indent_len}", f"{ln}.{indent_len + 2}")
                    elif after.startswith("#"):
                        self.editor.delete(f"{ln}.{indent_len}", f"{ln}.{indent_len + 1}")
                else:
                    self.editor.insert(f"{ln}.{indent_len}", "# ")

        self._on_editor_change()
        return "break"

    def _on_return(self, _event: tk.Event) -> str:
        if self._ac_popup is not None:
            self._accept_autocomplete()
            return "break"
        line_idx = self.editor.index(tk.INSERT).split(".")[0]
        line_text = self.editor.get(f"{line_idx}.0", f"{line_idx}.end")
        indent = re.match(r"^\s*", line_text).group(0)
        if line_text.rstrip().endswith(":"):
            indent += "    "
        self.editor.insert(tk.INSERT, "\n" + indent)
        self._on_editor_change()
        return "break"

    def _on_up_down(self, event: tk.Event) -> Optional[str]:
        if self._ac_popup is None or self._ac_listbox is None:
            return None
        cur = self._ac_listbox.curselection()
        idx = cur[0] if cur else 0
        total = self._ac_listbox.size()
        if total == 0:
            return None
        idx = (idx - 1) % total if event.keysym == "Up" else (idx + 1) % total
        self._ac_listbox.selection_clear(0, tk.END)
        self._ac_listbox.selection_set(idx)
        self._ac_listbox.see(idx)
        return "break"

    def _on_key_release(self, event: tk.Event) -> None:
        self._on_editor_change()
        if event.keysym in ("Up", "Down", "Left", "Right", "Return", "Tab", "Escape", "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return
        self._update_autocomplete()

    # --- IntelliSense Popup ---

    def _trigger_autocomplete(self) -> str:
        self._update_autocomplete(force=True)
        return "break"

    def _update_autocomplete(self, force: bool = False) -> None:
        line_start = self.editor.index(f"{tk.INSERT} linestart")
        line_prefix = self.editor.get(line_start, tk.INSERT)
        full_text = self.editor.get("1.0", "end-1c")
        text_before = self.editor.get("1.0", tk.INSERT)

        matches, word_col = intellisense.get_completions(
            full_text=full_text,
            line_prefix=line_prefix,
            mode=self.mode_var.get(),
            force=force,
            text_before_cursor=text_before,
        )
        if not matches:
            self._hide_autocomplete()
            return

        self._show_autocomplete_popup(matches, line_start, word_col)

    def _show_autocomplete_popup(self, matches: List[Tuple[str, str, str]], line_start: str, word_col: int) -> None:
        self._ac_matches = matches
        line_num = line_start.split(".")[0]
        self._ac_word_start = f"{line_num}.{word_col}"

        bbox = self.editor.bbox(tk.INSERT)
        if not bbox:
            self._hide_autocomplete()
            return

        x = self.editor.winfo_rootx() + bbox[0]
        y = self.editor.winfo_rooty() + bbox[1] + bbox[3] + 2
        popup_h = min(len(self._ac_matches), 8) * 20 + 8
        screen_h = self.root.winfo_screenheight()
        if y + popup_h > screen_h - 30:
            y = max(0, self.editor.winfo_rooty() + bbox[1] - popup_h - 2)

        if self._ac_popup is None:
            self._ac_popup = tk.Toplevel(self.root)
            self._ac_popup.wm_overrideredirect(True)
            self._ac_listbox = tk.Listbox(
                self._ac_popup,
                width=48,
                height=min(len(self._ac_matches), 8),
                bg="#fff7e6",
                fg=FG_DARK,
                selectbackground=ACCENT_GREEN,
                selectforeground="white",
                font=("Consolas", 10),
                bd=1,
                relief=tk.SOLID,
            )
            self._ac_listbox.pack()
            self._ac_listbox.bind("<ButtonRelease-1>", lambda _e: self._accept_autocomplete())
            self._ac_listbox.bind("<Double-Button-1>", lambda _e: self._accept_autocomplete())

        assert self._ac_listbox is not None
        self._ac_listbox.delete(0, tk.END)
        for kw, _snip, desc in self._ac_matches:
            self._ac_listbox.insert(tk.END, f"{kw:<15} | {desc}")
        self._ac_listbox.config(height=len(self._ac_matches))
        self._ac_listbox.selection_set(0)
        self._ac_popup.wm_geometry(f"+{x}+{y}")

    def _accept_autocomplete(self) -> None:
        if self._ac_popup is None or self._ac_listbox is None or not self._ac_matches:
            return
        sel = self._ac_listbox.curselection()
        idx = sel[0] if sel else 0
        _kw, raw_snippet, _desc = self._ac_matches[idx]

        line_idx = self._ac_word_start.split(".")[0]
        line_text = self.editor.get(f"{line_idx}.0", f"{line_idx}.end")
        base_indent = re.match(r"^\s*", line_text).group(0)
        lines = raw_snippet.split("\n")
        indented_snippet = ("\n" + base_indent).join(lines)

        cursor_offset = indented_snippet.find("$0")
        clean_snippet = indented_snippet.replace("$0", "")

        self.editor.delete(self._ac_word_start, tk.INSERT)
        self.editor.insert(self._ac_word_start, clean_snippet)
        if cursor_offset != -1:
            self.editor.mark_set(tk.INSERT, f"{self._ac_word_start}+{cursor_offset}c")
        else:
            self.editor.mark_set(tk.INSERT, f"{self._ac_word_start}+{len(clean_snippet)}c")

        self._hide_autocomplete()
        self._on_editor_change()
        self.editor.focus_set()

    def _hide_autocomplete(self) -> None:
        if self._ac_popup is not None:
            self._ac_popup.destroy()
            self._ac_popup = None
            self._ac_listbox = None
            self._ac_matches = []

    # --- Chuyen doi .vpy <-> .py ---

    def _on_mode_change(self) -> None:
        target_mode = self.mode_var.get()
        if target_mode == self._active_mode:
            return
        self._hide_autocomplete()
        if self._convert_editor_code(target_mode):
            self._active_mode = target_mode
            self._sync_family_lang_from_mode(target_mode)
            if 0 <= self._active_tab_idx < len(self._tabs):
                self._tabs[self._active_tab_idx].mode = target_mode
            self._update_status_bar()
        else:
            self.mode_var.set(self._active_mode)
            self._sync_family_lang_from_mode(self._active_mode)

    def toggle_convert_mode(self) -> None:
        pairs = {
            ".vpy": ".py",
            ".py": ".vpy",
            ".vhtml": ".html",
            ".html": ".vhtml",
            ".vcss": ".css",
            ".css": ".vcss",
            ".vjs": ".js",
            ".js": ".vjs",
        }
        target_mode = pairs.get(self._active_mode, ".py")
        self.mode_var.set(target_mode)
        self._on_mode_change()

    def _convert_editor_code(self, target_mode: str) -> bool:
        src = self.editor.get("1.0", "end-1c")
        if not src.strip():
            return True

        pair = (self._active_mode, target_mode)
        valid_pairs = (
            (".vpy", ".py"),
            (".py", ".vpy"),
            (".vhtml", ".html"),
            (".html", ".vhtml"),
            (".vcss", ".css"),
            (".css", ".vcss"),
            (".vjs", ".js"),
            (".js", ".vjs"),
        )
        if pair not in valid_pairs:
            return True

        try:
            if pair == (".vpy", ".py"):
                converted = transpiler.transpile_vpy_to_py(src)
            elif pair == (".py", ".vpy"):
                converted = transpiler.transpile_py_to_vpy(src)
            elif pair == (".vhtml", ".html"):
                converted = web_transpiler.transpile_vhtml_to_html(src)
            elif pair == (".html", ".vhtml"):
                converted = web_transpiler.transpile_html_to_vhtml(src)
            elif pair == (".vcss", ".css"):
                converted = web_transpiler.transpile_vcss_to_css(src)
            elif pair == (".css", ".vcss"):
                converted = web_transpiler.transpile_css_to_vcss(src)
            elif pair == (".vjs", ".js"):
                converted = js_transpiler.transpile_vjs_to_js(src)
            else:
                converted = js_transpiler.transpile_js_to_vjs(src)
        except Exception as exc:
            msg, hint, line_num = error_translator.explain_transpile_error(exc)
            self._clear_console()
            self._append_console(f"[Loi chuyen doi] {msg}\n", "err")
            if hint:
                self._append_console(f"{hint}\n", "hint")
            if line_num is not None:
                self.editor.tag_add("err_line", f"{line_num}.0", f"{line_num}.end+1c")
            return False

        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", converted)
        self._on_editor_change()
        self._clear_console()
        self._append_console(f"[OK] Da chuyen code sang che do {target_mode}!\n", "ok")
        return True

    # --- Editor Helpers ---

    def _change_font(self, delta: int) -> None:
        self.font_size = max(9, min(22, self.font_size + delta))
        self.editor.config(font=("Consolas", self.font_size))
        self.gutter.config(font=("Consolas", self.font_size))
        self.editor.tag_configure("kw", font=("Consolas", self.font_size, "bold"))
        self.editor.tag_configure("fn", font=("Consolas", self.font_size, "bold"))
        self.editor.tag_configure("cmt", font=("Consolas", self.font_size, "italic"))
        self.editor.tag_configure("brace_match", font=("Consolas", self.font_size, "bold"))

    def _on_editor_change(self, _event=None) -> None:
        if self.current_file is None:
            detected = intellisense.detect_code_mode(self.editor.get("1.0", "end-1c"))
            if detected != self._active_mode:
                self._active_mode = detected
                self.mode_var.set(detected)
                self._sync_family_lang_from_mode(detected)
                if 0 <= self._active_tab_idx < len(self._tabs):
                    tab = self._tabs[self._active_tab_idx]
                    tab.mode = detected
                    if tab.title.startswith("Bai_") and "." in tab.title:
                        tab.title = tab.title.rsplit(".", 1)[0] + detected
                        self._render_tab_bar()
        self._update_line_numbers()
        self._highlight_syntax()
        self._highlight_matching_brace()
        self._update_status_bar()
        self._schedule_diagnostics()
        if 0 <= self._active_tab_idx < len(self._tabs):
            mod = self.editor.edit_modified()
            if self._tabs[self._active_tab_idx].modified != mod:
                self._tabs[self._active_tab_idx].modified = mod
                self._render_tab_bar()

    def _update_status_bar(self) -> None:
        pos = self.editor.index(tk.INSERT)
        line, col = pos.split(".")
        mode_labels = {
            ".vpy": "Python Viet (.vpy)",
            ".py": "Python goc (.py)",
            ".vhtml": "Web Viet (.vhtml)",
            ".html": "HTML goc (.html)",
            ".vcss": "CSS Viet (.vcss)",
            ".css": "CSS goc (.css)",
            ".vjs": "JS Viet (.vjs)",
            ".js": "JavaScript goc (.js)",
        }
        lbl = mode_labels.get(self.mode_var.get(), self.mode_var.get())
        self.status_right.config(text=f"Dong {line}, Cot {int(col) + 1}  |  Tu nhan dien: {lbl}")

    def _update_line_numbers(self) -> None:
        line_count = int(self.editor.index("end-1c").split(".")[0])
        nums = "\n".join(str(i) for i in range(1, line_count + 1))
        self.gutter.config(state=tk.NORMAL)
        self.gutter.delete("1.0", tk.END)
        self.gutter.insert("1.0", nums)
        self.gutter.config(state=tk.DISABLED)

    def _highlight_syntax(self) -> None:
        for tag in ("kw", "builtin", "fn", "num", "attr", "str", "cmt"):
            self.editor.tag_remove(tag, "1.0", tk.END)

        text = self.editor.get("1.0", "end-1c")
        mode = self.mode_var.get()

        if mode in (".vhtml", ".html"):
            for m in re.finditer(r"</?[a-zA-Z][a-zA-Z0-9_-]*|/?>", text):
                self.editor.tag_add("kw", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
            for m in re.finditer(r"\b([a-zA-Z_-]+)\s*(?==|:)", text):
                self.editor.tag_add("attr", f"1.0+{m.start(1)}c", f"1.0+{m.end(1)}c")
            for m in re.finditer(r"<!--[\s\S]*?-->", text):
                self.editor.tag_add("cmt", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        elif mode in (".vcss", ".css"):
            for m in re.finditer(r"^\s*([.#]?[a-zA-Z_-][a-zA-Z0-9_-]*)\s*(?=\{)", text, re.MULTILINE):
                self.editor.tag_add("kw", f"1.0+{m.start(1)}c", f"1.0+{m.end(1)}c")
            for m in re.finditer(r"\b([a-zA-Z-]+)\s*(?=:)", text):
                self.editor.tag_add("attr", f"1.0+{m.start(1)}c", f"1.0+{m.end(1)}c")
            for m in re.finditer(r"/\*[\s\S]*?\*/", text):
                self.editor.tag_add("cmt", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        elif mode in (".vjs", ".js"):
            js_kw = r"\b(bien|hangso|ham|trave|neu|hoacla|nguoclai|voi|trongkhi|dunglai|tieptuc|Dung|Sai|Rong|let|const|var|function|return|if|else|for|while|break|continue|true|false|null)\b"
            js_builtin = r"\b(ghilog|thongbao|hoinho|xacnhan|tim_ma|tim_the|tim_tatca|langnghe|noidung|ma_html|giatri|console|log|alert|prompt|confirm|document|window)\b"
            for m in re.finditer(js_kw, text):
                self.editor.tag_add("kw", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
            for m in re.finditer(js_builtin, text):
                self.editor.tag_add("builtin", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
            for m in re.finditer(r"//[^\n]*|/\*[\s\S]*?\*/", text):
                self.editor.tag_add("cmt", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        else:
            kw_pat = (
                r"\b(neu|hoacla|nguoclai|voi|trong|trongkhi|dunglai|tieptuc|boqua|"
                r"ham|trave|lop|thu|batloi|cuoicung|dung|tu|la|va|hoac|khong|Dung|Sai|Rong|"
                r"if|elif|else|for|in|while|break|continue|pass|def|return|class|"
                r"try|except|finally|import|from|as|and|or|not|True|False|None)\b"
            )
            builtin_pat = (
                r"\b(in|nhap|dodai|dayso|songuyen|sothuc|chuoi|danhsach|tudien|taphop|"
                r"tinhtong|lonnhat|nhonhat|sapxep|lamtron|tuyetdoi|giatrituyetdoi|kieu|"
                r"luythua|mofile|tatca|batky|print|input|len|range|int|float|str|list|"
                r"dict|set|sum|max|min|sorted|round|abs|type|open|pow|all|any)\b"
            )
            for m in re.finditer(kw_pat, text):
                self.editor.tag_add("kw", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
            for m in re.finditer(builtin_pat, text):
                self.editor.tag_add("builtin", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
            for m in re.finditer(r"\b(?:ham|def)\s+([A-Za-z_]\w*)", text):
                self.editor.tag_add("fn", f"1.0+{m.start(1)}c", f"1.0+{m.end(1)}c")
            for m in re.finditer(r"#.*", text):
                self.editor.tag_add("cmt", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

        for m in re.finditer(r"\b\d+(?:\.\d+)?\b", text):
            self.editor.tag_add("num", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for m in re.finditer(r'(".*?"|\'.*?\')', text):
            self.editor.tag_add("str", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    def _schedule_diagnostics(self) -> None:
        if self._diag_after_id is not None:
            self.root.after_cancel(self._diag_after_id)
        self._diag_after_id = self.root.after(450, self._run_diagnostics)

    def _run_diagnostics(self) -> Optional[str]:
        self._diag_after_id = None
        self.editor.tag_remove("lint_err", "1.0", tk.END)
        src = self.editor.get("1.0", "end-1c")
        if not src.strip():
            if self.running_proc is None:
                self.status_left.config(text="San sang")
            return None

        mode = self.mode_var.get()
        err_msg: Optional[str] = None
        err_line: Optional[int] = None

        if mode in (".vpy", ".py"):
            try:
                py_code = transpiler.transpile_vpy_to_py(src) if mode == ".vpy" else src
                compile(py_code, "<vide>", "exec")
            except Exception as exc:
                if isinstance(exc, SyntaxError):
                    err_line = exc.lineno
                    err_msg = f"Loi cu phap (dong {err_line}): Kiem tra dau ':', ngoac '()' hoac thut le."
                else:
                    msg, _hint, err_line = error_translator.explain_transpile_error(exc)
                    err_msg = msg
        elif mode in (".vhtml", ".html"):
            void_tags = {"img", "hinh", "br", "xuongdong", "hr", "duongke", "input", "onhap", "meta", "thongtin", "link", "lienket_file", "lienket_css"}
            stack: List[Tuple[str, int]] = []
            for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9_-]*)([^<>]*?)(/?)>", src):
                slash, tag, _, self_close = m.groups()
                low_tag = tag.lower()
                if self_close or low_tag in void_tags:
                    continue
                line_no = src[: m.start()].count("\n") + 1
                if not slash:
                    stack.append((low_tag, line_no))
                else:
                    if stack and stack[-1][0] == low_tag:
                        stack.pop()
                    elif not stack:
                        err_line = line_no
                        err_msg = f"Thua the dong </{tag}> o dong {line_no}."
                        break
            if err_msg is None and stack:
                unclosed, err_line = stack[-1]
                err_msg = f"Chua dong the <{unclosed}> mo o dong {err_line}."

        if err_msg and err_line is not None:
            self.editor.tag_add("lint_err", f"{err_line}.0", f"{err_line}.end")
            if self.running_proc is None:
                self.status_left.config(text=err_msg)
            return err_msg

        if self.running_proc is None:
            self.status_left.config(text="San sang (Khong co loi cu phap)")
        return None

    def format_code(self) -> str:
        """Lam dep va can le chuan cho code dang mo (Ctrl+Shift+F)."""
        src = self.editor.get("1.0", "end-1c")
        if not src.strip():
            return "break"

        mode = self.mode_var.get()
        if mode in (".vhtml", ".html"):
            formatted = self._format_html_like(src)
        else:
            lines = [ln.replace("\t", "    ").rstrip() for ln in src.splitlines()]
            cleaned: List[str] = []
            blank_streak = 0
            for ln in lines:
                if ln == "":
                    blank_streak += 1
                    if blank_streak <= 1:
                        cleaned.append(ln)
                else:
                    blank_streak = 0
                    cleaned.append(ln)
            formatted = "\n".join(cleaned).rstrip() + "\n"

        cursor = self.editor.index(tk.INSERT)
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", formatted)
        try:
            self.editor.mark_set(tk.INSERT, cursor)
        except tk.TclError:
            pass
        self._on_editor_change()
        self.status_left.config(text="Da can le va lam dep code!")
        return "break"

    @staticmethod
    def _format_html_like(src: str) -> str:
        void_tags = {"img", "hinh", "br", "xuongdong", "hr", "duongke", "input", "onhap", "meta", "thongtin", "link", "lienket_file", "lienket_css", "!doctype"}
        raw_lines = [ln.strip() for ln in src.splitlines() if ln.strip()]
        out: List[str] = []
        indent = 0
        for ln in raw_lines:
            is_closing_only = bool(re.match(r"^</[a-zA-Z][a-zA-Z0-9_-]*>", ln))
            if is_closing_only:
                indent = max(0, indent - 1)
            out.append(("    " * indent) + ln)
            m_open = re.match(r"^<([a-zA-Z!][a-zA-Z0-9_-]*)\b[^>]*>$", ln)
            if m_open and not ln.endswith("/>") and m_open.group(1).lower() not in void_tags:
                if f"</{m_open.group(1)}>" not in ln:
                    indent += 1
        return "\n".join(out) + "\n"

    def _highlight_matching_brace(self) -> None:
        self.editor.tag_remove("brace_match", "1.0", tk.END)
        pairs = {"(": ")", "[": "]", "{": "}", ")": "(", "]": "[", "}": "{"}
        opening = {"(", "[", "{"}

        pos = self.editor.index(tk.INSERT)
        ch_after = self.editor.get(pos, f"{pos}+1c")
        ch_before = self.editor.get(f"{pos}-1c", pos) if pos != "1.0" else ""

        if ch_after in pairs:
            target_pos = pos
            ch = ch_after
        elif ch_before in pairs:
            target_pos = f"{pos}-1c"
            ch = ch_before
        else:
            return

        match_ch = pairs[ch]
        step = 1 if ch in opening else -1
        depth = 0
        cur = target_pos
        for _ in range(2000):
            c = self.editor.get(cur, f"{cur}+1c")
            if not c:
                break
            if c == ch:
                depth += 1
            elif c == match_ch:
                depth -= 1
                if depth == 0:
                    self.editor.tag_add("brace_match", target_pos, f"{target_pos}+1c")
                    self.editor.tag_add("brace_match", cur, f"{cur}+1c")
                    return
            nxt = self.editor.index(f"{cur}{'+' if step > 0 else '-'}1c")
            if nxt == cur:
                break
            cur = nxt

    def show_find_bar(self) -> str:
        self.find_bar.pack(fill=tk.X, before=self.editor.master)
        self.find_entry.focus_set()
        self.find_entry.select_range(0, tk.END)
        return "break"

    def hide_find_bar(self) -> str:
        self.editor.tag_remove("find_match", "1.0", tk.END)
        self.find_bar.pack_forget()
        self.editor.focus_set()
        return "break"

    def find_next(self) -> None:
        query = self.find_entry.get()
        self.editor.tag_remove("find_match", "1.0", tk.END)
        if not query:
            return

        start = "1.0"
        while True:
            idx = self.editor.search(query, start, stopindex=tk.END, nocase=True)
            if not idx:
                break
            end = f"{idx}+{len(query)}c"
            self.editor.tag_add("find_match", idx, end)
            start = end

        nxt = self.editor.search(query, f"{tk.INSERT}+1c", stopindex=tk.END, nocase=True)
        if not nxt:
            nxt = self.editor.search(query, "1.0", stopindex=tk.END, nocase=True)
        if nxt:
            self.editor.mark_set(tk.INSERT, nxt)
            self.editor.see(nxt)

    # --- File Actions ---

    def _load_lesson(self, name: str, confirm: bool = True) -> None:
        ext, content = snippets.LESSONS[name]
        self._open_or_create_tab(name, None, content, ext, modified=False)
        self._clear_console()

    def new_file(self) -> None:
        num = len(self._tabs) + 1
        self._open_or_create_tab(f"Bai_{num}.vpy", None, "", ".vpy", modified=False)

    def load_file(self, path: Path) -> None:
        content = path.read_text(encoding="utf-8")
        ext = path.suffix.lower()
        vi_map = {".py": ".vpy", ".html": ".vhtml", ".css": ".vcss", ".js": ".vjs"}
        target_mode = vi_map.get(ext, ext if ext in (".vpy", ".vhtml", ".vcss", ".vjs") else ".vpy")

        if ext in vi_map and content.strip():
            try:
                if ext == ".py":
                    content = transpiler.transpile_py_to_vpy(content)
                elif ext == ".html":
                    content = web_transpiler.transpile_html_to_vhtml(content)
                elif ext == ".css":
                    content = web_transpiler.transpile_css_to_vcss(content)
                elif ext == ".js":
                    content = js_transpiler.transpile_js_to_vjs(content)
            except Exception:
                target_mode = ext

        self._open_or_create_tab(path.name, path, content, target_mode, modified=False)

    def open_file(self) -> None:
        start_dir = str(self.workspace_dir) if self.workspace_dir else str(Path.home())
        path_str = filedialog.askopenfilename(
            initialdir=start_dir,
            filetypes=[("vpy / Python / Web", "*.vpy *.py *.vhtml *.html *.vcss *.css"), ("Tat ca file", "*.*")],
        )
        if path_str:
            self.load_file(Path(path_str))

    def save_file(self) -> bool:
        path = self.current_file
        if not path:
            ext = self.mode_var.get()
            start_dir = str(self.workspace_dir) if self.workspace_dir else str(Path.home())
            path_str = filedialog.asksaveasfilename(
                initialdir=start_dir,
                defaultextension=ext,
                filetypes=[("vpy / Python / Web", "*.vpy *.py *.vhtml *.html"), ("Tat ca file", "*.*")],
            )
            if not path_str:
                return False
            path = Path(path_str)
            self.current_file = path

        text_to_write = self.editor.get("1.0", "end-1c")
        ext = path.suffix.lower()
        cur_mode = self.mode_var.get()
        if (cur_mode, ext) == (".vpy", ".py"):
            text_to_write = transpiler.transpile_vpy_to_py(text_to_write)
        elif (cur_mode, ext) == (".vhtml", ".html"):
            text_to_write = web_transpiler.transpile_vhtml_to_html(text_to_write)
        elif (cur_mode, ext) == (".vcss", ".css"):
            text_to_write = web_transpiler.transpile_vcss_to_css(text_to_write)
        elif (cur_mode, ext) == (".vjs", ".js"):
            text_to_write = js_transpiler.transpile_vjs_to_js(text_to_write)

        path.write_text(text_to_write, encoding="utf-8")
        self.editor.edit_modified(False)
        if 0 <= self._active_tab_idx < len(self._tabs):
            self._tabs[self._active_tab_idx].modified = False
            self._tabs[self._active_tab_idx].title = path.name
        self.root.title(f"vide - {path.name}")
        self._render_tab_bar()
        self._refresh_live_preview_on_save(path)
        self.refresh_explorer()
        self.status_left.config(text=f"Da luu: {path.name}")
        return True

    def show_dictionary(self) -> None:
        """Mo cua so tra cuu nhanh cu phap tieng Viet cho Python & Web."""
        win = tk.Toplevel(self.root)
        win.title("Tu dien cu phap tieng Viet - vide")
        win.geometry("620x460")
        win.configure(bg=BG_WARM)

        txt = tk.Text(win, wrap=tk.WORD, padx=14, pady=12, bg=BG_EDITOR, fg=FG_DARK, font=("Consolas", 10), border=0)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        guide = (
            "=== 1. PYTHON TIENG VIET (.vpy) ===\n"
            "  in(...)               -> print(...)         In ra man hinh\n"
            "  nhap(...)             -> input(...)         Hoi nguoi dung nhap\n"
            "  neu / hoacla / nguoclai-> if / elif / else  Re nhanh dieu kien\n"
            "  voi i trong dayso(5): -> for i in range(5): Vong lap\n"
            "  trongkhi ...:         -> while ...:         Lap theo dieu kien\n"
            "  ham ten(): / trave    -> def ten(): / return Tao ham & tra ket qua\n"
            "  Dung / Sai / Rong     -> True / False / None\n"
            "  dung random           -> import random      Nhap thu vien\n"
            "  tinhtong / lonnhat    -> sum / max          Tinh toan danh sach\n\n"
            "=== 2. WEB TIENG VIET (.vhtml / .vcss) ===\n"
            "  <trang><dau><than>    -> <html><head><body> Khung trang web\n"
            "  <tieude>...</tieude>  -> <h1>...</h1>       Tieu de lon\n"
            "  <doan>...</doan>      -> <p>...</p>         Doan van ban\n"
            "  <hop lop=\"...\">       -> <div class=\"...\">  Khoi chua\n"
            "  <nut>...</nut>        -> <button>...</button> Nut bam\n"
            "  <hinh nguon=\"...\">    -> <img src=\"...\">    Chen hinh anh\n"
            "  <kieu>...</kieu>      -> <style>...</style>  Trang tri CSS\n"
            "  mau-chu / mau-nen     -> color / background-color\n"
            "  can-le: giua          -> text-align: center\n"
            "  le-trong / bo-goc     -> padding / border-radius\n\n"
            "=== 3. JAVASCRIPT TIENG VIET (.vjs) ===\n"
            "  bien x = 5;           -> let x = 5;\n"
            "  hangso pi = 3.14;     -> const pi = 3.14;\n"
            "  ham chao() { ... }    -> function chao() { ... }\n"
            "  ghilog(\"...\");        -> console.log(\"...\");\n"
            "  thongbao(\"...\");      -> alert(\"...\");\n"
            "  tim_ma(\"nut\").langnghe(\"click\", ...) -> getElementById(\"nut\").addEventListener(...)\n"
            "  .noidung / .giatri    -> .textContent / .value\n"
        )
        txt.insert("1.0", guide)
        txt.config(state=tk.DISABLED)

    def _on_close(self) -> None:
        self._save_active_tab_state()
        for idx, tab in enumerate(self._tabs):
            if tab.modified:
                ans = messagebox.askyesnocancel("Chua luu bai", f"'{tab.title}' co thay doi chua luu. Luu truoc khi thoat?")
                if ans is None:
                    return
                if ans is True:
                    self.switch_tab(idx)
                    if not self.save_file():
                        return
        self.stop_code()
        if self._live_server is not None:
            self._live_server.shutdown()
            self._live_server.server_close()
            self._live_server = None
        self.root.destroy()

    # --- Console & Execution ---

    def _append_console(self, text: str, tag: str = "") -> None:
        self.console.config(state=tk.NORMAL)
        if tag:
            self.console.insert(tk.END, text, tag)
        else:
            self.console.insert(tk.END, text)
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def _clear_console(self) -> None:
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.config(state=tk.DISABLED)
        self.editor.tag_remove("err_line", "1.0", tk.END)

    def send_stdin(self) -> None:
        if self.running_proc is None or self.running_proc.stdin is None:
            return
        text = self.stdin_entry.get()
        self.stdin_entry.delete(0, tk.END)
        self._append_console(f"{text}\n", "inp")
        try:
            self.running_proc.stdin.write(text + "\n")
            self.running_proc.stdin.flush()
        except OSError:
            pass

    def _ensure_live_server(self, root_dir: Path) -> int:
        if self._live_server is not None and self._live_root == root_dir and self._live_port is not None:
            return self._live_port

        if self._live_server is not None:
            self._live_server.shutdown()
            self._live_server.server_close()

        ide_ref = self

        class _LiveHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, directory=str(root_dir), **kwargs)

            def do_GET(self) -> None:
                if self.path.split("?")[0] == "/__vide_version":
                    payload = str(ide_ref._live_version).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
                super().do_GET()

            def log_message(self, format: str, *args) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), _LiveHandler)
        self._live_server = server
        self._live_root = root_dir
        self._live_port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return self._live_port

    def _inject_live_reload(self, html_doc: str) -> str:
        script = (
            "\n<script>\n"
            "(function(){\n"
            f"  var v='{self._live_version}';\n"
            "  setInterval(function(){\n"
            "    fetch('/__vide_version?t='+Date.now()).then(r=>r.text()).then(nv=>{\n"
            "      if(nv && nv!==v){ location.reload(); }\n"
            "    }).catch(function(){});\n"
            "  }, 600);\n"
            "})();\n"
            "</script>\n"
        )
        if "</body>" in html_doc.lower():
            return re.sub(r"</body>", script + "</body>", html_doc, count=1, flags=re.IGNORECASE)
        return html_doc + script

    def _write_live_preview(self, src: str, mode: str, base_dir: Path) -> Path:
        html_code = web_transpiler.transpile_vhtml_to_html(src) if mode == ".vhtml" else src
        full_doc = web_transpiler.ensure_html_document(html_code)
        live_doc = self._inject_live_reload(full_doc)
        preview_path = base_dir / "_vide_preview.html"
        preview_path.write_text(live_doc, encoding="utf-8")
        return preview_path

    def _refresh_live_preview_on_save(self, saved_path: Path) -> None:
        if self._live_server is None or self._live_root is None:
            return
        ext = saved_path.suffix.lower()
        if ext in (".vhtml", ".html"):
            src = self.editor.get("1.0", "end-1c")
            self._live_version += 1
            self._write_live_preview(src, self.mode_var.get(), self._live_root)
            self._last_html_tab_idx = self._active_tab_idx
        elif ext in (".vcss", ".css", ".vjs", ".js"):
            self._live_version += 1
            if self._last_html_tab_idx is not None and 0 <= self._last_html_tab_idx < len(self._tabs):
                html_tab = self._tabs[self._last_html_tab_idx]
                self._write_live_preview(html_tab.content, html_tab.mode, self._live_root)

    def run_code(self) -> None:
        if self.running_proc is not None:
            return
        self._hide_autocomplete()
        self._clear_console()
        self._stderr_chunks = []
        src = self.editor.get("1.0", "end-1c")
        mode = self.mode_var.get()

        if mode in (".vhtml", ".html"):
            base_dir = self.current_file.parent if self.current_file is not None else Path(tempfile.gettempdir())
            self._last_html_tab_idx = self._active_tab_idx
            self._live_version += 1
            port = self._ensure_live_server(base_dir)
            self._write_live_preview(src, mode, base_dir)
            url = f"http://127.0.0.1:{port}/_vide_preview.html"
            webbrowser.open(url)
            self._append_console(
                f"[OK] Da mo Live Preview tai: {url}\n"
                "  Meo: Khi ban bam Luu (Ctrl+S) o file HTML hoac CSS, trinh duyet se tu cap nhat!\n",
                "ok",
            )
            self.status_left.config(text="Live Preview dang chay (tu cap nhat khi Luu)")
            return

        if mode in (".vjs", ".js"):
            node_exe = shutil.which("node")
            if not node_exe:
                self._append_console("[!] May chua cai Node.js de chay file JS doc lap. Hay nhung vao file HTML bang <lienket_js file=\"...\"> va bam Chay tren file HTML!", "hint")
                return
            js_code = js_transpiler.transpile_vjs_to_js(src) if mode == ".vjs" else src
            fd, tmp_name = tempfile.mkstemp(suffix=".js", prefix="vide_js_")
            os.close(fd)
            tmp_js = Path(tmp_name)
            tmp_js.write_text(js_code, encoding="utf-8")
            try:
                proc = subprocess.run([node_exe, str(tmp_js)], capture_output=True, text=True, encoding="utf-8", errors="replace")
                if proc.stdout:
                    self._append_console(proc.stdout)
                if proc.returncode != 0:
                    self._append_console(f"\n[Loi JavaScript]\n{proc.stderr}\n", "err")
                    self.status_left.config(text="Co loi JavaScript")
                else:
                    self._append_console("\n[OK] Chay JavaScript xong!\n", "ok")
                    self.status_left.config(text="Chay JS xong")
            finally:
                tmp_js.unlink(missing_ok=True)
            return

        if mode == ".vpy":
            try:
                py_code = transpiler.transpile_vpy_to_py(src)
            except Exception as exc:
                msg, hint, line_num = error_translator.explain_transpile_error(exc)
                self._append_console(f"[Loi] {msg}\n", "err")
                if hint:
                    self._append_console(f"{hint}\n", "hint")
                if line_num is not None:
                    self.editor.tag_add("err_line", f"{line_num}.0", f"{line_num}.end+1c")
                    self.editor.see(f"{line_num}.0")
                self.status_left.config(text="Co loi cu phap")
                return
        else:
            py_code = src

        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.stdin_entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.status_left.config(text="Dang chay chuong trinh...")
        if re.search(r"\b(nhap|input)\s*\(", src):
            self.stdin_entry.focus_set()

        def _worker() -> None:
            from .commands import get_active_python

            fd, tmp_name = tempfile.mkstemp(suffix=".py", prefix="vpy_ide_")
            os.close(fd)
            tmp_path = Path(tmp_name)
            tmp_path.write_text(py_code, encoding="utf-8")

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            try:
                self.running_proc = subprocess.Popen(
                    [get_active_python(), "-u", str(tmp_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    env=env,
                )

                def _read_stdout() -> None:
                    assert self.running_proc and self.running_proc.stdout
                    while True:
                        ch = self.running_proc.stdout.read(1)
                        if not ch:
                            break
                        self.root.after(0, lambda c=ch: self._append_console(c))

                def _read_stderr() -> None:
                    assert self.running_proc and self.running_proc.stderr
                    data = self.running_proc.stderr.read()
                    if data:
                        self._stderr_chunks.append(data)

                t_out = threading.Thread(target=_read_stdout, daemon=True)
                t_err = threading.Thread(target=_read_stderr, daemon=True)
                t_out.start()
                t_err.start()
                t_out.join()
                t_err.join()
                rc = self.running_proc.wait()
                stderr_all = "".join(self._stderr_chunks)
                self.root.after(0, lambda: self._on_run_finished(rc, stderr_all))
            finally:
                self.running_proc = None
                tmp_path.unlink(missing_ok=True)

        threading.Thread(target=_worker, daemon=True).start()

    def stop_code(self) -> None:
        if self.running_proc is not None:
            self.running_proc.terminate()
            self._append_console("\n[!] Da dung chuong trinh theo yeu cau.\n", "hint")
            self.status_left.config(text="Da dung")

    def _on_run_finished(self, rc: int, stderr: str) -> None:
        self.run_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.stdin_entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)

        if rc == 0:
            self._append_console("\n[OK] Chuong trinh chay xong khong co loi!\n", "ok")
            self.status_left.config(text="Chay xong (Khong loi)")
            return

        self.status_left.config(text="Chuong trinh co loi")
        msg, hint, line_num = error_translator.explain_python_error(stderr)
        self._append_console(f"\n[Loi] {msg}\n", "err")
        if hint:
            self._append_console(f"{hint}\n", "hint")
        if stderr:
            self._append_console(f"\n--- Chi tiet tu Python ---\n{stderr}\n", "raw")

        if line_num is not None:
            self.editor.tag_add("err_line", f"{line_num}.0", f"{line_num}.end+1c")
            self.editor.see(f"{line_num}.0")


def launch_ide(initial_file: Optional[str] = None) -> int:
    root = tk.Tk()
    VPyIDE(root, initial_target=initial_file)
    root.mainloop()
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    target = args[0] if args else None
    return launch_ide(initial_file=target)
